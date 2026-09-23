# IEEE 1801-2024: initial normative review

The user supplied IEEE Std 1801-2024, revision of IEEE Std 1801-2018, on
2026-09-23. This edition defines UPF 4.0 and is now the initial normative target.
The supplied 614-page PDF has SHA-256
`e42c0fbe6367a70f89439fad5aeb6ecbf69781fd80001b6f5d56a241bfc233a5`.
The licensed PDF and locally extracted text are not distributed in this repository.
The earlier access audit in POWER_COLLATERAL.md is historical; normative text
access is no longer a blocker. Design-owner intent and independent runtime oracles
remain missing.

This is a partial review, not a completed conformance matrix or a claim that the
current parser implements this edition. Existing executable behavior remains the
legacy bounded dialect. References below use printed page numbers; PDF page
numbers are one higher for these clauses.

| Existing or needed command | Normative anchor | Initial comparison and required work |
|---|---|---|
| `create_power_domain` | 6.21, p.135 | The standard makes elements optional and supports additional domain/supply/update behavior. The prototype requires elements and uses a simplified path ownership model. Validate scope, effective extent and all applicable exceptions before claiming conformance. |
| `create_supply_net` | 6.25 and 6.25.1, p.151 | The standard accepts a list of net names. The prototype treats one positional word as one name. Domain/reuse are legacy arguments; resolution, scope, tunneling and supply-state behavior are not implemented. A braced list must not silently become one literal net name in a future edition-specific parser. |
| `set_domain_supply_net` | 6.46, pp.195–196 | Explicitly legacy. It associates the primary supply set's power/ground functions with nets. The prototype's name checks do not implement supply-set semantics; retaining legacy syntax must not imply complete semantic support. |
| `set_isolation` | 6.48, syntax p.198 | Elements, clamp value and isolation signal are optional in the standard's syntax, while the prototype requires all three. The standard admits additional clamp forms and strategy options. Existing source-side matching is not a normative implementation of strategy applicability, precedence, location or inserted behavior. The rest of this clause and referenced clauses still require review. |
| `upf_version` | 6.61, p.243 | The optional argument documents the intended UPF version; the command returns the tool's interpretation version. This edition specifies 4.0. Accepting a version marker alone cannot establish conformance, and a non-evaluating dialect cannot silently pretend to provide general Tcl return/substitution behavior. The opt-in audit now records this statement without executing a return value; legacy mode still rejects it. See EDITION_AUDIT_EVIDENCE.md. |

## Implementation order grounded in these findings

1. Separate the existing dialect from an explicit 2024 capability contract. Keep
   unsupported commands/options visible; never label the legacy parser UPF 4.0
   merely because it accepts a version string.
2. Read the common command rules and referenced scope/supply-set sections, then
   finish the command/option/semantic matrix. Distinguish syntax recognition,
   static interpretation, elaborated binding and runtime behavior.
3. Add only a clause-backed, independently tested slice. First candidates are
   accurate supply-name list handling and edition identification, followed by
   domain/supply bindings. Preserve existing fixtures in the legacy lane.
4. Review full isolation applicability and corruption/scheduling semantics before
   implementing the OpenTitan lifecycle clamp case or Icarus runtime hooks.
   The six published clamp requirements remain useful input, not complete intent.

The standard's complete runtime semantics, normative examples, exceptions,
conformance requirements and Icarus/UVM integration have not yet been audited.
This document records exactly what has been read so far and what still needs
proof. This initial review is historical; subsequent supply-list and edition-audit slices are recorded in their evidence documents. No production qualification is established.
