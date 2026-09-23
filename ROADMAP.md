# QD-UPF: UPF implementation for power-aware Icarus Verilog and UVM

## Intended product (scope clarified 2026-09-23)

QD-UPF will be a UPF tool and an extension of Icarus Verilog and its UVM flow, implementing edition-pinned power-aware elaboration and simulation. Static intent analysis is a supporting capability, not the final product. The current executable is only a bounded static prototype; no power-aware runtime is implemented today.

## Current capability

Baseline `f4dd49d634f8661806b75c55d01ba46c7ce1268a`: 22 Python tests;
CI runs `python3 -m unittest discover -s tests -v`. Four command families use
bounded non-evaluating Tcl syntax. Checks cover names, supplies, ownership and
source-side isolation declarations against hand-authored topology. No edition
conformance is established; the README explicitly says normative IEEE text was
not consulted. `isolation_declared` is not implemented isolation.

## Stages and interfaces

1. **Next useful slice:** target the user-supplied IEEE 1801-2024 (UPF 4.0) and
   make a command/option/semantic-clause conformance table against legally
   accessible authoritative text. Obtain access before implementing additional
   semantics. Retain the legacy bounded dialect as such; a requested unsupported
   edition must fail. Validate normative examples and reject unsupported Tcl
   without evaluation. No added commands justified only by tutorials.
2. **Pinned pilot:** use Caliptra `caliptra_top` generic and OpenTitan Earlgrey
   power-manager hierarchy as topology targets. First acquire design-owner
   power intent, library isolation/retention/level-shifter semantics, operating
   states and synthesis configuration. These inputs are currently unverified;
   there is no claimed ready-to-run power-aware pilot. Hand-created intent is a
   QD integration fixture, not authoritative design intent. Derive crossings
   from a parser-backed elaborated RTL or netlist and compare with an independent
   elaborator; reconcile names and hierarchy before applying intent.
3. **Semantic expansion:** domains and supply sets/connections first; then legal
   power states and state-dependent isolation; then voltage-dependent level
   shifting, retention save/restore, and power switches/control ordering. At each
   step compare intended strategy with mapped cells, controls, locations, clamp
   values and supply connectivity. Emit unsupported/UNKNOWN for unmodeled library
   semantics, hierarchy, modes or power states. Keep declaration and implementation
   results separate.
4. **Icarus/UVM implementation:** pin an Icarus compiler/runtime revision and UVM
   implementation, then establish a reviewed compiler/runtime integration point.
   Do not assume VPI callbacks or a source wrapper can implement all required
   scheduling semantics. First implement a normative, bounded domain on/off and
   isolation slice with four-state corruption and recovery behavior. Then add
   retention save/restore, supply/power-state transitions, level-shifter models
   and switch behavior according to the edition conformance table. Expose power
   control and observation to plain SV and UVM sequences/monitors; support checking
   of power-up/down ordering, reset interactions and expected corruption. Every
   runtime semantic needs a positive, negative and boundary timing test plus an
   independent power-aware simulator oracle. Unsupported semantics must fail
   elaboration or remain explicitly UNKNOWN, never silently simulate as always-on.
5. **Production qualification:** edition + exact command subset + named domains,
   states, mapped library and design revisions. Compare against a licensed
   independent low-power checker and power-aware simulation with injected intent
   and implementation faults. Qualify only that intersection; no dynamic power,
   analog voltage, IR-drop, or full IEEE 1801 conformance claim. Qualification
   must include the QD-UPF Icarus runtime and UVM integration, not just checks
   against someone else's simulator.

## Evidence and release criteria

- Inputs: edition, UPF, elaborated design/netlist, cell-library semantics,
  operating-state matrix and constraints. Outputs: located parser/semantic
  diagnostics, ownership and crossing inventory, intent-to-cell matches,
  unsupported coverage and evidence references in deterministic JSON.
  Runtime inputs additionally include power-control stimulus and the pinned
  Icarus/UVM build; outputs include the power-aware simulation artifact, resolved
  domain/supply bindings, timestamped power/corruption/retention events and UVM
  results. Preserve the ordinary no-UPF simulation lane and its passing behavior.
- Corpus: retain 22 cases; add edition-specific legal/illegal examples, Tcl
  nesting/escaping adversarial cases, sink/source isolation, voltage/state
  combinations, missing controls, swapped clamps, retention ordering, switch
  controls, hierarchical names and unconnected supplies. Fixtures only for faults.
  Add event-order/delta-cycle tests, X/Z propagation, repeated power cycling,
  isolation-before-off, retention ordering and reset while a domain is off.
- Oracles: normative clause table with edition/page/section citations, second
  parser/checker, independent netlist tracing and power-aware simulation. A
  tutorial is context, not normative authority. Record access limitations.
- Version matrix: Python 3.9/3.14, IEEE 1801-2024 initially; pin frontend,
  synthesis tool, library revision and independent simulator/checker versions
  when owner inputs are available. Other editions remain unsupported.
  Pin Icarus compiler and vvp runtime together, the UVM source revision and any
  simulator extension ABI; requalify on changes to these versions.
- Targets: 10k intent commands and 100k derived crossings <=30 s/2 GiB;
  per-state pilot simulation <=10 min; timeouts are incomplete evidence.
  Initial runtime target: <=2x wall time and <=2x peak RSS versus the same pinned
  always-on fixture, median of five runs with identical stimulus and build flags;
  report overhead separately from compile/elaboration cost. This is unmeasured.
- Release: every supported semantic has authoritative traceability and positive,
  negative and boundary cases; all pilot crossings accounted for; all state/cell
  comparisons reviewed; zero unexplained oracle disagreement. Until normative
  and design-owner inputs exist, remain an explicitly bounded prototype.

## Qualification contract

This is a staged plan, not a production qualification claim. No stage is earned
by a green unit suite alone. Keep existing passing behavior and raw diagnostics.
Do not change application RTL/DV, disable assertions, or introduce dummy VIP to
make a pilot pass. A failed pilot is an artifact to retain, not a test to remove.

Named pilot pins (full SHAs, never floating branches):
- Caliptra RTL v2.1.2: `49370266d12cb0c4a8f71b3a0ff7e54ba7d4866e`, generic simulation primitives;
  Adams Bridge v2.0.3: `b77e3d899e828d626cfc2a0d26a6b5704cc121e0` when needed.
- OpenTitan: `7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19`; select the named IP fileset, generic technology,
  and record all FuseSoC flags, parameters, generated files, and their digests.
  The later configuration-blocker evidence at `a78922f14a8cc20c7ee569f322a04626f2ac6127`
  is a separate revision, not interchangeable qualification evidence.

Every release candidate needs an immutable evidence bundle: tool Git SHA and
binary hashes; OS/architecture, Python/compiler/simulator/solver versions;
design and submodule SHAs; top, parameters, defines, ordered files/includes,
constraints, libraries, seeds; input/output hashes; exact argv, raw stdout/stderr,
exit codes, wall time and peak RSS. Repeat twice in clean independent workspaces;
compare canonical findings and explain any nondeterminism. Archive the bundle
with the release and publish a supported/unsupported configuration table.

Review every expected finding and every oracle disagreement. Seed known defects
in separate test fixtures and require their detection; never mutate pilot RTL.
Unknowns and exclusions remain counted and visible. Waivers require a stable
finding/configuration identity, owner, independent reviewer, rationale, evidence
hash/link, expiry, and revalidation on any relevant input change. A waiver is a
review disposition, not a proof. No unreviewed waiver or unexplained oracle
mismatch is allowed in the qualified scope. Outside that scope report UNKNOWN
or a clear unsupported error. A version or dependency change reopens qualification.

Performance numbers below are acceptance targets, not measurements. Measure on
a named Linux x86-64 runner with 8 cores and 16 GiB RAM; record hardware and
median of five runs. No automatic threshold relaxation. macOS arm64 is a second
portability lane, not a substitute for the qualification runner.

## Portfolio priority and real-flow blockers

1. **QD-Lint first:** source/configuration fidelity is prerequisite evidence for
   every downstream analysis. OpenTitan pinmux's conditional `fileset_ip` versus
   `fileset_top` selects different register packages. A local pinned matrix probe
   at `a78922f...` reproduced an omitted-package failure from wrong setup flags;
   it was not an RTL defect. Caliptra's generic/technology primitive roots also
   select different sources. Audit these choices before caching or baselining.
2. **QD-BFM second:** Caliptra's README requires licensed Avery AXI and QVIP AHB
   dependencies in full UVMF flows. A bounded independent AXI adapter is useful,
   but cannot cure simulator/UVM/firmware dependencies or replace their APIs.
3. **QD-CDC, then QD-DFD:** real reset/synchronizer and lifecycle/debug cones are
   available; getting complete elaboration and constraints is the next blocker.
   VCD observations and cell annotations cannot establish safety on their own.
4. **QD-UPF and QD-DFT:** do standards/library/topology inventory now; owner-approved
   power intent and scan-mapped collateral are unverified. Do not invent these
   inputs or mistake lack of collateral for a demonstrated design failure.

Primary source anchors (review pinned source, not just current web documentation):
- [Caliptra dependency and configuration README](https://github.com/chipsalliance/caliptra-rtl/blob/49370266d12cb0c4a8f71b3a0ff7e54ba7d4866e/README.md).
- [OpenTitan pinmux fileset selection](https://github.com/lowRISC/opentitan/blob/a78922f14a8cc20c7ee569f322a04626f2ac6127/hw/ip/pinmux/pinmux_reg.core).
- [OpenTitan lifecycle architecture](https://github.com/lowRISC/opentitan/tree/7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19/hw/ip/lc_ctrl/doc).
- [OpenTitan TL DV agent](https://github.com/lowRISC/opentitan/tree/7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19/hw/dv/sv/tl_agent).

## Updated standards and collateral evidence

See POWER_COLLATERAL.md and pilots/opentitan-clamp-inventory.json. The current
IEEE GET catalog offers 1801-2024 with account sign-in; 2018 is superseded. Edition
choice needs reconciliation with accessible normative text before semantic work.
The provisional 2018 target is not a conformance claim. No normative clauses have
yet been verified; no automatic substitution of a newer edition is allowed.

OpenTitan's pinned synthesis collateral does provide six nonzero lifecycle clamp
requirements. Therefore the blocker is incomplete power intent and binding data,
not absence of every power-related artifact. Prioritize a future implementation
check for these six exact port bits: match elaborated endpoints, resolve strategy
applicability and precedence using the selected edition, verify library clamp and
control polarity, then test power transitions with the real lifecycle decoder.
The nonzero list alone does not specify the remaining bits, power states, drivers,
control sequencing or a complete isolation strategy. Never invent those inputs.

## Supplied normative text, 2026-09-23

The user has supplied IEEE 1801-2024. It supersedes the provisional 2018 target;
see IEEE1801_2024_REVIEW.md for its file identity and initial clause comparison.
Normative text access is resolved. The common rules, semantic matrix, independent
oracles, design bindings and power-aware runtime still require implementation and
verification. The earlier access notes above describe the pre-upload state.
