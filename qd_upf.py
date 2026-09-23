"""QD-UPF v0: static consistency checker for a small, explicit subset of IEEE 1801 UPF.

The UPF file is tokenized with a bounded subset of Tcl word rules. Nothing is ever
evaluated: variable, command, and backslash substitution are rejected. This is an
intent-consistency check, not power-aware simulation or implementation signoff.
"""
import argparse
import bisect
import json
import sys

VERSION = "0.1.0"
WS = " \t\r\f\v"
EXIT = {"ok": 0, "error": 1, "unknown": 3}  # 2 is argparse usage / unreadable input

# command -> (required options, optional options); every option takes one value
# and every command takes exactly one positional name.
SCHEMA = {
    "create_power_domain": ({"-elements"}, set()),
    "create_supply_net": (set(), {"-domain"}),
    "set_domain_supply_net": ({"-primary_power_net", "-primary_ground_net"}, set()),
    "set_isolation": ({"-domain", "-elements", "-clamp_value", "-isolation_signal"},
                      {"-isolation_sense", "-applies_to",
                       "-isolation_power_net", "-isolation_ground_net"}),
}
ENUMS = {"-clamp_value": ("0", "1"), "-isolation_sense": ("high", "low"),
         "-applies_to": ("inputs", "outputs", "both")}


class ParseError(Exception):
    def __init__(self, pos, msg):
        super().__init__(msg)
        self.pos = pos


def lex(text):
    """Split text into commands of (word, offset) using a no-substitution Tcl subset."""
    cmds, words, i, n = [], [], 0, len(text)

    def cont(j):  # backslash-newline: Tcl turns it (plus leading blanks) into one space
        return text.startswith("\\\n", j)

    while i < n:
        c = text[i]
        if c in WS or cont(i):
            i += 2 if cont(i) else 1
        elif c in "\n;":
            if words:
                cmds.append(words)
                words = []
            i += 1
        elif c == "#" and not words:  # comment only where a command may start
            while i < n and text[i] != "\n":
                i += 2 if text[i] == "\\" else 1
        else:
            start, buf = i, []
            if text.startswith("{*}", i):
                raise ParseError(i, "argument expansion {*} is not supported")
            if c in '{"':
                close, depth, i = ("}" if c == "{" else '"'), 1, i + 1
                while True:
                    if i >= n:
                        raise ParseError(start, f"missing close-{'brace' if c == '{' else 'quote'}")
                    ch = text[i]
                    if ch == "\\":
                        if not cont(i):
                            raise ParseError(i, "backslash substitution is not supported")
                        i += 2
                        while i < n and text[i] in " \t":
                            i += 1
                        buf.append(" ")
                        continue
                    if c == '"' and ch in "$[":
                        raise ParseError(i, f"Tcl substitution '{ch}' is not supported")
                    if c == "{" and ch == "{":
                        depth += 1
                    elif ch == close:
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    buf.append(ch)
                    i += 1
                if i < n and text[i] not in WS + "\n;" and not cont(i):
                    raise ParseError(i, "extra characters after close-brace or close-quote")
            else:
                while i < n and text[i] not in WS + "\n;" and not cont(i):
                    ch = text[i]
                    if ch in "$[":
                        raise ParseError(i, f"Tcl substitution '{ch}' is not supported")
                    if ch in '\\{}"':
                        raise ParseError(i, f"unsupported character '{ch}' in bare word")
                    buf.append(ch)
                    i += 1
            words.append(("".join(buf), start))
    if words:
        cmds.append(words)
    return cmds


def split_list(s):
    """Tcl list split for braced option values; nested braces group, nothing else is special."""
    out, i, n = [], 0, len(s)
    while True:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            return out
        j = i
        if s[i] == "{":
            depth = 0
            while j < n:
                depth += {"{": 1, "}": -1}.get(s[j], 0)
                if depth == 0:
                    break
                j += 1
            if j >= n or (j + 1 < n and not s[j + 1].isspace()):
                raise ValueError("unbalanced braces in list")
            out.append(s[i + 1:j])
            i = j + 1
        else:
            while j < n and not s[j].isspace():
                j += 1
            if any(ch in '{}"\\' for ch in s[i:j]):
                raise ValueError(f"unsupported list element {s[i:j]!r}")
            out.append(s[i:j])
            i = j


def covers(element, path):
    return path == element or path.startswith(element + "/")


def check(upf_text, upf_path, topology, topo_path, topo_error=None):
    diags = []
    text = upf_text.replace("\r\n", "\n")
    starts = [0] + [k + 1 for k, ch in enumerate(text) if ch == "\n"]

    def loc(pos):
        line = bisect.bisect_right(starts, pos)
        return f"{upf_path}:{line}:{pos - starts[line - 1] + 1}"

    def diag(sev, code, where, msg):
        diags.append({"severity": sev, "code": code, "location": where, "message": msg})

    report = {"tool": "qd-upf", "version": VERSION, "diagnostics": diags,
              "domains": {}, "crossings": []}

    # --- syntax: any failure here stops before semantic checks (fail closed) ---
    try:
        cmds = lex(text)
    except ParseError as e:
        diag("error", "PARSE", loc(e.pos), str(e))
        cmds = []
    parsed = []
    for words in cmds:
        (name, pos), args = words[0], words[1:]
        if name not in SCHEMA:
            diag("error", "UNSUPPORTED", loc(pos), f"unsupported command '{name}'")
            continue
        required, optional = SCHEMA[name]
        opts, positional, bad, k = {}, [], False, 0
        while k < len(args):
            w, wpos = args[k]
            if w.startswith("-"):
                if w not in required | optional:
                    diag("error", "BAD_ARGS", loc(wpos), f"{name}: unsupported option '{w}'")
                    bad = True
                elif w in opts:
                    diag("error", "BAD_ARGS", loc(wpos), f"{name}: option '{w}' given twice")
                    bad = True
                elif k + 1 >= len(args):
                    diag("error", "BAD_ARGS", loc(wpos), f"{name}: option '{w}' needs a value")
                    bad = True
                else:
                    opts[w] = args[k + 1]
                k += 2
            else:
                positional.append(args[k])
                k += 1
        if len(positional) != 1 or not positional[0][0]:
            diag("error", "BAD_ARGS", loc(pos), f"{name}: expected exactly one name, got "
                 + (" ".join(repr(w) for w, _ in positional) or "none"))
            bad = True
        for opt in sorted(required - opts.keys()):
            diag("error", "BAD_ARGS", loc(pos), f"{name}: missing required option '{opt}'")
            bad = True
        for opt, (val, vpos) in sorted(opts.items()):
            if opt in ENUMS and val not in ENUMS[opt]:
                diag("error", "BAD_ARGS", loc(vpos), f"{name}: {opt} must be one of "
                     f"{'|'.join(ENUMS[opt])}, got {val!r}")
                bad = True
            elif opt == "-elements":
                try:
                    lst = split_list(val)
                except ValueError as e:
                    diag("error", "BAD_ARGS", loc(vpos), f"{name}: -elements: {e}")
                    bad = True
                    continue
                if not lst or not all(lst):
                    diag("error", "BAD_ARGS", loc(vpos), f"{name}: -elements must list names")
                    bad = True
                opts[opt] = (lst, vpos)
            elif not val:
                diag("error", "BAD_ARGS", loc(vpos), f"{name}: {opt} is empty")
                bad = True
        if not bad:
            parsed.append((name, positional[0], opts, pos))
    if diags:
        report["result"] = "error"
        return report

    # --- semantics: single pass in source order, so references must be declared first ---
    domains, nets, isolations, owners = report["domains"], {}, {}, {}

    def known(kind, table, val, vpos):
        if val not in table:
            diag("error", "UNKNOWN_REF", loc(vpos), f"unknown {kind} '{val}'")
        return val in table

    for name, (obj, opos), opts, pos in parsed:
        if name == "create_power_domain":
            if obj in domains:
                diag("error", "DUPLICATE", loc(opos), f"power domain '{obj}' already declared")
                continue
            elements, epos = opts["-elements"]
            domains[obj] = {"elements": elements, "location": loc(opos)}
            for e in elements:
                if e in owners:
                    same = owners[e] == obj
                    diag("error", "DUPLICATE" if same else "MULTI_OWNER", loc(epos),
                         f"element '{e}' listed twice in '{obj}'" if same else
                         f"element '{e}' owned by both '{owners[e]}' and '{obj}'")
                else:
                    owners[e] = obj
        elif name == "create_supply_net":
            if obj in nets:
                diag("error", "DUPLICATE", loc(opos), f"supply net '{obj}' already declared")
            elif "-domain" not in opts or known("power domain", domains, *opts["-domain"]):
                nets[obj] = loc(pos)
        elif name == "set_domain_supply_net":
            if not known("power domain", domains, obj, opos):
                continue
            if "primary_power_net" in domains[obj]:
                diag("error", "DUPLICATE", loc(pos), f"primary supplies for '{obj}' set twice")
                continue
            pwr, gnd = opts["-primary_power_net"], opts["-primary_ground_net"]
            if all([known("supply net", nets, *pwr), known("supply net", nets, *gnd)]):
                domains[obj]["primary_power_net"] = pwr[0]
                domains[obj]["primary_ground_net"] = gnd[0]
        elif name == "set_isolation":
            dom, dpos = opts["-domain"]
            if not known("power domain", domains, dom, dpos):
                continue
            key = f"{dom}/{obj}"
            if key in isolations:
                diag("error", "DUPLICATE", loc(opos), f"isolation strategy '{key}' already declared")
                continue
            ok = all([known("supply net", nets, *opts[o])
                      for o in ("-isolation_power_net", "-isolation_ground_net") if o in opts])
            elements, epos = opts["-elements"]
            for e in elements:
                owner = max((d for d in owners if covers(d, e)), key=len, default=None)
                if owners.get(owner) != dom:
                    ok = False
                    diag("error", "UNKNOWN_ELEMENT", loc(epos), f"isolation element '{e}' is "
                         + (f"owned by '{owners[owner]}'" if owner else "in no power domain")
                         + f", not '{dom}'")
            if ok:
                isolations[key] = {"domain": dom, "elements": elements,
                                   "applies_to": opts.get("-applies_to", ("both",))[0]}

    for d, info in domains.items():
        if "primary_power_net" not in info:
            diag("error", "MISSING_SUPPLY", info["location"],
                 f"power domain '{d}' has no primary power/ground (set_domain_supply_net)")

    # --- topology crossings ---
    if topo_error or not isinstance(topology, list):
        diag("error", "TOPOLOGY", topo_path, topo_error or "topology must be a JSON list of crossings")
        topology = []
    elif not topology and len(domains) > 1:
        diag("unknown", "TOPOLOGY_UNKNOWN", topo_path,
             "no crossings listed; isolation coverage cannot be evaluated")
    seen = set()
    for i, c in enumerate(topology):
        where = f"{topo_path}[{i}]"
        fields = ("name", "source", "destination", "signal")
        if not isinstance(c, dict) or not all(isinstance(c.get(f), str) and c[f] for f in fields):
            diag("unknown", "TOPOLOGY_UNKNOWN", where,
                 "crossing needs non-empty string fields: " + ", ".join(fields))
            report["crossings"].append({"index": i, "status": "unknown"})
            continue
        row = {f: c[f] for f in fields}
        row["status"], row["strategies"] = "unknown", []
        report["crossings"].append(row)
        if c["name"] in seen:
            diag("error", "DUPLICATE", where, f"crossing '{c['name']}' listed twice")
        seen.add(c["name"])
        src, dst = domains.get(c["source"]), domains.get(c["destination"])
        for f, d in (("source", src), ("destination", dst)):
            if d is None:
                diag("error", "UNKNOWN_REF", where, f"unknown {f} power domain '{c[f]}'")
        if src is None or dst is None:
            continue
        owner = max((e for e in owners if covers(e, c["signal"])), key=len, default=None)
        if owners.get(owner) != c["source"]:
            diag("error", "UNKNOWN_ELEMENT", where, f"signal '{c['signal']}' is "
                 + (f"owned by '{owners[owner]}'" if owner else "in no power domain")
                 + f", not source '{c['source']}'")
        if "primary_power_net" not in src or "primary_power_net" not in dst:
            continue  # MISSING_SUPPLY already reported; coverage stays unknown
        if c["source"] == c["destination"] or src["primary_power_net"] == dst["primary_power_net"]:
            row["status"] = "not_required"
            continue
        # ponytail: conservative -- no power states, so any primary-power difference
        # requires source-side output isolation; add add_power_state support to relax.
        row["strategies"] = [k for k, s in isolations.items()
                             if s["domain"] == c["source"] and s["applies_to"] != "inputs"
                             and any(covers(e, c["signal"]) for e in s["elements"])]
        if row["strategies"]:
            row["status"] = "isolation_declared"
        else:
            row["status"] = "missing_isolation"
            diag("error", "MISSING_ISOLATION", where,
                 f"crossing '{c['name']}' ({c['source']} -> {c['destination']}, "
                 f"{c['signal']}) has differing primary power and no declared isolation")

    sevs = {d["severity"] for d in diags}
    report["result"] = "error" if "error" in sevs else "unknown" if sevs else "ok"
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="qd-upf", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    chk = sub.add_parser("check", help="check UPF intent against a crossing topology")
    chk.add_argument("upf")
    chk.add_argument("--topology", required=True, help="JSON list of crossings")
    chk.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args(argv)
    try:
        with open(a.upf, encoding="utf-8") as f:
            upf_text = f.read()
        with open(a.topology, encoding="utf-8") as f:
            topo_text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"qd-upf: error: {e}", file=sys.stderr)
        return 2
    try:
        topology, topo_error = json.loads(topo_text), None
    except json.JSONDecodeError as e:
        topology, topo_error = None, f"invalid JSON at line {e.lineno} column {e.colno}: {e.msg}"
    r = check(upf_text, a.upf, topology, a.topology, topo_error)
    if a.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        for d in r["diagnostics"]:
            print(f"{d['location']}: {d['severity']}: [{d['code']}] {d['message']}")
        for c in r["crossings"]:
            if "name" in c:
                print(f"crossing {c['name']} ({c['source']} -> {c['destination']}, "
                      f"{c['signal']}): {c['status']}"
                      + (f" by {', '.join(c['strategies'])}" if c["strategies"] else ""))
        errs = sum(d["severity"] == "error" for d in r["diagnostics"])
        print(f"qd-upf: {r['result']} ({errs} errors, {len(r['diagnostics']) - errs} unknown)"
              " -- static intent check of a UPF subset, not signoff")
    return EXIT[r["result"]]


if __name__ == "__main__":
    sys.exit(main())
