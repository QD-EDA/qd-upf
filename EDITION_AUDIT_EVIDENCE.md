# IEEE 1801-2024 version-statement audit

`--edition 1801-2024` selects an explicit normative reference and a conservative
static audit contract. It does **not** select a conforming UPF interpreter. The
existing checks retain their legacy bounded semantics. The default and explicit
`--edition legacy` retain the previous report shape, results and command support.

## Clause-backed behavior

The supplied licensed IEEE Std 1801-2024 PDF, SHA256
`e42c0fbe6367a70f89439fad5aeb6ecbf69781fd80001b6f5d56a241bfc233a5`, section 6.61,
printed p.243 (PDF page 244), defines upf_version with an optional string argument.
The argument documents the intended version of subsequent commands; it is not a
specified interpreter-mode switch. The command also has a runtime return value.
The 2024 edition specifies the version string 4.0; mixed-version interpretation
is not defined by that clause. The licensed text is not redistributed here.

The audit recognizes zero or one argument, accepts exactly `4.0` when present,
and records each statement's location and intended_version (null for a query).
Repeated identical declarations are retained. Unsupported strings, including
3.0, 5.0, 4 and empty strings, produce UNSUPPORTED_VERSION before semantic checks.
Multiple arguments produce BAD_ARGS. This is the supported audit policy; it is
not a claim that other editions cannot define those version strings.

`runtime_return_value` is always null: the non-evaluating checker did not execute
the query and must not claim to have returned 4.0. Command/variable substitution
still fails PARSE. No mode attempts to evaluate Tcl or change runtime behavior.

Every audit report includes `standard` with the reference edition, version,
`conformance_established: false`, scope and unimplemented capability groups.
Syntax failures retain this metadata. Otherwise, EDITION_UNVERIFIED is emitted
as UNKNOWN after the existing static checks. Exit is 3 absent errors, or 1 when
any error exists. No input currently earns exit 0 in this audit mode. Errors are
never downgraded to UNKNOWN. This gate will need clause-specific qualification
before any future supported scope can legitimately pass.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
/usr/bin/python3 -m unittest discover -s tests -v
./qd-upf check examples/valid.upf --topology examples/crossings.json --json
# Legacy result ok, exit 0.
./qd-upf check examples/valid.upf --topology examples/crossings.json --edition 1801-2024 --json
# Existing crossing results retained; edition qualification unknown, exit 3.
./qd-upf check examples/version_audit.upf --topology examples/empty_topology.json --edition 1801-2024 --json
# Located 4.0 declaration recorded, runtime return null, exit 3.
```

The version fixture is QD-owned syntax collateral, not authoritative chip intent.
Six new tests cover default preservation, located version declarations, absent and
query-only markers, repeated markers, unsupported strings/arity, substitution,
error precedence, CLI gating and metadata on malformed input. They failed before
the new option existed. All 34 tests pass on Python 3.14.7 and Apple Python 3.9.6.
The previously added independent Tcl list oracle also still passes; Tcl does not
supply an independent UPF semantic implementation. Version semantics are checked
against the supplied normative clause, not a commercial simulator.

The real OpenTitan collateral at clean commit
`7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19`,
`hw/top_earlgrey/syn/chip_earlgrey_asic_nonzero_upf_vals.tcl`, remains UNSUPPORTED
in both modes: its Tcl set command is not complete supported UPF intent. The
existing pinned six-clamp inventory still reproduces and exits UNKNOWN (3).
No application sources or power intent were rewritten to create a passing case.
Caliptra owner intent remains unavailable; no Caliptra UPF-conformance pilot is
claimed. Commands, raw reports, source hashes and test logs are retained locally
in `../evidence/upf-edition-audit/`, not published release artifacts.

## Remaining work

Full Tcl/query evaluation, scope and supply-set semantics, normative isolation
applicability, topology binding, implementation checks, power states, corruption,
retention and Icarus/UVM runtime integration remain unimplemented. This change
makes the edition boundary machine-readable; it adds no dynamic power behavior,
IEEE conformance certification or production qualification.
