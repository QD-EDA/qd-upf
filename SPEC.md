# Product scope

QD-UPF will be a UPF tool and an extension of Icarus Verilog and its UVM flow, implementing edition-pinned power-aware elaboration and simulation. Static intent analysis is a supporting capability, not the final product. The current executable is only a bounded static prototype; no power-aware runtime is implemented today.

The historical v0 specification below describes the existing prototype, not a limit on the intended product. The staged implementation and qualification contract is in ROADMAP.md.

# QD-UPF v0 scope

Build a small, honest static checker for an explicitly supported subset of IEEE 1801 UPF. It is not a power-aware simulator or implementation signoff tool. Its first job is to detect inconsistent power intent before Caliptra-style RTL integration.

CLI: `qd-upf check intent.upf --topology crossings.json [--json]`. The topology is a simple, documented JSON list of named source domain, destination domain, and signal crossings; do not pretend to derive it from RTL. Parse a bounded UPF/Tcl lexical subset safely without executing Tcl, shell, substitutions, or external commands. Support ordinary quoted/braced words, comments, and line continuations for the selected commands. Reject unsupported commands explicitly with source locations.

Supported intent: `create_power_domain` with `-elements`; `create_supply_net`; `set_domain_supply_net` with primary power/ground nets; `set_isolation` with domain, signal, and clamp; and any additional command strictly necessary to express a valid isolated crossing. Confirm each command's syntax against public standard/vendor documentation and cite it in README. Do not infer that presence of an isolation declaration proves its implementation.

Checks: duplicate names; unknown or multiply-owned elements; missing/unknown primary supplies; malformed/unknown isolation references; uncovered cross-domain output when independently powered domains are declared. Emit deterministic diagnostics, a nonzero status for errors, and a machine-readable JSON option. A topology without enough information is reported as unknown rather than passed.

Tests: a valid two-domain example with isolation; duplicate domain; unknown supply; missing isolation; unsupported Tcl substitution fails closed; braced multiword parsing and comments. Use Python standard library if possible. Freeze these cases before implementation; no hidden network or source edits. Keep changes only in this repository. Add a concise README, Apache-2.0 license, and runnable test command. Do not commit, push, or create a GitHub repo; coordinator owns publication.

## Supply-name list correction

Interpret create_supply_net's positional argument as a bounded Tcl list, creating
each unique name once per IEEE 1801-2024 6.25.1. Reject empty or unsupported list
forms before semantics. Preserve the single-name interface and existing duplicate
checks across commands. This does not add other supply or runtime semantics.
