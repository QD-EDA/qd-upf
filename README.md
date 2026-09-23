# qd-upf

## Product direction

QD-UPF will be a UPF tool and an extension of Icarus Verilog and its UVM flow, implementing edition-pinned power-aware elaboration and simulation. Static intent analysis is a supporting capability, not the final product. The current executable is only a bounded static prototype; no power-aware runtime is implemented today.

## Current prototype

QD-UPF v0 is a small static checker for an explicit subset of IEEE 1801 (UPF) power intent.
It looks for inconsistent power intent before RTL integration, for example in Caliptra-style designs.

**What this tool is not.** It is not a power-aware simulator, and it does not check implementation. It is not UPF signoff.
- A result of `ok` only means this subset found no inconsistency against the topology you supplied.
- `isolation_declared` means a matching `set_isolation` strategy exists. It does not prove that the isolation is implemented, controlled, or correct.

## Usage

Requires Python 3.9+ (tested on 3.9.6 and 3.14.7) and uses only the standard library. Nothing needs to be installed.

```sh
./qd-upf check examples/valid.upf --topology examples/crossings.json          # exit 0
./qd-upf check examples/missing_isolation.upf --topology examples/crossings.json   # exit 1
./qd-upf check examples/valid.upf --topology examples/empty_topology.json --json  # exit 3
python3 -m qd_upf check intent.upf --topology crossings.json [--json]          # same, from repo root
```

| exit | result    | meaning |
|------|-----------|---------|
| 0    | `ok`      | no errors or unknowns in the supported subset |
| 1    | `error`   | at least one error diagnostic |
| 2    | –         | usage error or unreadable input file |
| 3    | `unknown` | no errors, but the topology lacked the information to decide |

Text diagnostics use the form `file:line:col: severity: [CODE] message`. Topology diagnostics are located as `file[index]`.
`--json` prints a report with sorted keys: `result`, `diagnostics`, `domains`, and `crossings`.
`--json` always emits the report, even for malformed topology JSON (`TOPOLOGY` error).
Diagnostic order is deterministic: command diagnostics in source order, then `MISSING_SUPPLY`, then topology diagnostics in list order.

## Topology (`--topology`)

The topology is supplied by hand. qd-upf does not derive it from RTL. It is a JSON list with one object per crossing:

```json
[{"name": "core_irq", "source": "PD_CORE", "destination": "PD_AON", "signal": "u_core/irq"}]
```

All four fields must be non-empty strings. Unknown results come from these cases:
- A crossing is missing a field. That crossing is reported as `unknown`.
- The list is empty while more than one domain is declared. The whole run is reported as `unknown`, not passed.

## Supported UPF subset

Each command takes exactly one positional name, and each option takes exactly one value. Any other command or option is rejected with its `line:col`.
Option names must use ASCII `-`. Some published examples use typographic en-dashes (`–elements`), and those are rejected.

| command | required | optional |
|---|---|---|
| `create_power_domain <pd>` | `-elements {list}` | – |
| `create_supply_net <net>` | – | `-domain <pd>` |
| `set_domain_supply_net <pd>` | `-primary_power_net <net>` `-primary_ground_net <net>` | – |
| `set_isolation <strategy>` | `-domain <pd>` `-elements {list}` `-clamp_value 0\|1` `-isolation_signal <sig>` | `-isolation_sense high\|low` `-applies_to inputs\|outputs\|both` `-isolation_power_net <net>` `-isolation_ground_net <net>` |

`set_isolation_control` is not needed. UPF 2.x `set_isolation` carries `-isolation_signal` and `-isolation_sense` itself, as the ISLPED tutorial below shows.

### Syntax sources

The syntax was checked against the downloaded text of these sources. The PDFs typeset option dashes as en-dashes (`–domain`); they are normalized to `-` in the quotes below.
- IEEE Std 1801 (UPF) is the normative standard. Its full text was **not** consulted. The current GET catalog offers 1801-2024 with IEEE account sign-in; the 2018 edition is superseded and its direct PDF route requested subscription/member access in this session. See [the standards and collateral audit](POWER_COLLATERAL.md); do not infer availability from the older landing page alone.
- VLSI Tutorials, "UPF – Low Power VLSI". It shows `create_power_domain … -elements {…}` (including nested `{{a/b}}`), `create_supply_net … -domain`, `set_domain_supply_net … -primary_power_net … -primary_ground_net …`, and `set_isolation … -domain -isolation_power_net -isolation_ground_net -clamp_value -elements {…}`: <https://vlsitutorials.com/upf-low-power-vlsi/>
- R. Koster, J. Redmond, S. Ramachandra, "Failing to Fail: Achieving Success in Advanced Low Power Design using UPF", ISLPED 2014 tutorial (Mentor/Broadcom/Synopsys). It shows `set_isolation sw_iso_c0 -domain PD_IP -applies_to outputs -clamp_value 0 -isolation_signal iso -isolation_sense high -location self`, `-clamp_value {1}` (braced value), and `create_supply_net sw1_out_net` (no `-domain`): <https://islped.org/2014/files/Failing%20to%20fail%20UPF%20tutorial%20.pdf>
- A. Srivastava, M. Bhargava (Mentor Graphics), "Stepping into UPF 2.1 world", DVCon. It shows `set_isolation iso_tx -domain pd_tx … -applies_to outputs`, `set_isolation iso_rx -domain pd_rx … -applies_to inputs`, `set_isolation iso -domain pd_hardIP -applies_to both`, `create_power_domain … -elements {…}`, and backslash line continuation: <https://dvcon-proceedings.org/wp-content/uploads/stepping-into-upf-2-1-world-easy-solution-to-complex-power-aware-verification.pdf>
- Tcl(n) man page, rules [1] Commands, [4] Double quotes, [5] Argument expansion, [6] Braces, [7]–[9] substitutions, and [10] Comments: <https://www.tcl-lang.org/man/tcl8.6/TclCmd/Tcl.htm>

### Lexical subset (fails closed; Tcl is never evaluated)

- Words are separated by blanks. Commands are separated by newline or `;`. CRLF line endings are accepted.
- `#` starts a comment only where a command may begin. `;#` therefore gives a trailing comment.
- A backslash-newline (plus following blanks) acts as one space, including inside braces and comments.
- `{…}` braced words nest and are literal, so `{u_core/c[3]}` is fine. `"…"` quoted words are allowed only when they contain no `$`, `[`, or `\`.
- These are errors, reported at their location:
  - `$` variable substitution, `[` command substitution, and any other backslash escape
  - `{*}` argument expansion
  - an unclosed brace or quote, reported at its opening position
  - any character right after a closing brace or quote
- `-elements` values are split with Tcl list rules, where nested braces group.
- Any syntax or argument error stops the run before the semantic checks, so errors do not cascade.

## Checks

| code | condition |
|---|---|
| `PARSE`, `UNSUPPORTED`, `BAD_ARGS` | lexical error, unsupported command/option, missing/duplicate/empty option, bad `-clamp_value`/`-isolation_sense`/`-applies_to` value |
| `DUPLICATE` | domain, supply net, isolation strategy (per domain), element within a domain, primary supplies set twice, crossing name |
| `MULTI_OWNER` | the exact same element path listed in two domains (nested paths such as `a` and `a/b` in different domains are legal) |
| `UNKNOWN_REF` | reference to an undeclared domain or supply net (commands are processed in order, so declare before use) |
| `UNKNOWN_ELEMENT` | isolation element or crossing signal not owned (longest `/`-boundary prefix) by the named domain |
| `MISSING_SUPPLY` | domain without `set_domain_supply_net` |
| `MISSING_ISOLATION` | crossing between domains whose primary power nets differ, and no `set_isolation` in the source domain whose `-elements` covers the signal (`u_core` covers `u_core/irq`, not `u_corex/irq`) and whose `-applies_to` is not `inputs` |
| `TOPOLOGY_UNKNOWN` | crossing lacks fields, or no crossings are given for a multi-domain intent (severity `unknown`) |

## Known limits (v0)

- "Independently powered" means only that the two domains' primary power nets differ. There are no power states, so every such crossing needs source-side output isolation, including always-on → switchable crossings. This is conservative.
- Only source-domain isolation counts. Sink-side `-applies_to inputs` strategies are accepted but never cover a crossing.
- Supply nets share one flat namespace. For `create_supply_net -domain`, the only check is that the domain exists. `-reuse`, supply ports, supply sets, and `connect_supply_net` are unsupported.
- `-isolation_signal` is not checked against the design, because qd-upf has no RTL.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

## License

Apache License 2.0; see [LICENSE](LICENSE).

See [the staged qualification roadmap](ROADMAP.md) for named pilots, unsupported
cases, independent oracles, performance targets and release gates.

## Pinned power collateral

The [OpenTitan collateral audit](POWER_COLLATERAL.md) records six published
nonzero lifecycle clamp requirements and a reproducible inventory. It is not a
complete UPF file or proof of installed isolation. The full runtime and
edition-qualified semantics remain roadmap work.
