# qd-upf

A small **static checker for a subset of UPF (IEEE 1801) power intent**. It looks for inconsistencies before RTL integration. It is *not* a power-aware simulator and *not* UPF signoff; `ok` only means this subset found nothing wrong against the topology you supplied.

| | |
|---|---|
| Language | Python 3.9+ (standard library only) |
| Input | a `.upf` file plus a JSON topology of domain crossings |
| Status | Active prototype (Sep 2026) |
| License | Apache-2.0 |

## Run

```sh
./qd-upf check examples/valid.upf --topology examples/crossings.json            # exit 0
./qd-upf check examples/missing_isolation.upf --topology examples/crossings.json  # exit 1
python3 -m unittest discover -s tests -v
```

| Exit | Result | Meaning |
|---|---|---|
| 0 | `ok` | no errors or unknowns in the supported subset |
| 1 | `error` | at least one error diagnostic |
| 2 | n/a | usage error or unreadable input |
| 3 | `unknown` | no errors, but the topology could not decide |

## What it checks

| Code | Condition |
|---|---|
| `PARSE`, `UNSUPPORTED`, `BAD_ARGS` | lexical errors, unsupported commands or options |
| `DUPLICATE`, `MULTI_OWNER` | repeated domains, nets, strategies, elements; one element in two domains |
| `UNKNOWN_REF`, `UNKNOWN_ELEMENT` | undeclared domain or supply net; element not owned by the named domain |
| `MISSING_SUPPLY` | domain without a primary supply |
| `MISSING_ISOLATION` | crossing between differently powered domains with no source-side isolation covering the signal |
| `TOPOLOGY_UNKNOWN` | crossing information missing (severity `unknown`) |

Tcl is never evaluated; unsupported constructs fail closed. Limits and the supported subset: [docs/usage.md](docs/usage.md).
