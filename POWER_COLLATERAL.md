# Standards access and concrete power collateral

## Normative access audit, 2026-09-23

The [IEEE 1801-2018 landing page](https://standards.ieee.org/ieee/1801/6767/)
still mentions no-cost GET access, but marks the edition superseded by 2024.
The live [GET design automation catalog](https://ieeexplore.ieee.org/browse/standards/get-program/page/series?id=80)
lists 1801-2024, requires IEEE account sign-in, and says editions leave GET when
superseded. The normal PDF action on the 2018 document page opened a
subscription/member access dialog. No purchase, account creation or terms
acceptance was performed; no full normative PDF was obtained or consulted.
The earlier blanket statement that UPF is paywalled was too broad.

The roadmap's 2018 target remains provisional pending edition/access resolution.
The older edition and 2024 must not be treated as interchangeable. No new UPF
command or runtime semantic is implemented by this collateral audit.

| Capability | Current basis | Normative qualification |
|---|---|---|
| Domain elements and ownership | Existing bounded parser, tutorial examples | Clause mapping unverified |
| Supply-net declarations and primary nets | Existing bounded static checks | Clause mapping unverified |
| Isolation declaration matching | Source-side heuristic against supplied crossings | Applicability, precedence and implementation unverified |
| Tcl support | Non-evaluating lexical subset | General Tcl unsupported |
| Power states, corruption, retention, switches, level shifting | Not implemented | Unverified |
| Icarus/UVM power-aware runtime | Not implemented | Scheduling/integration point and independent oracle unverified |

A completed table must cite edition, clause and relevant exceptions after reading
legally accessible normative text, then add independent positive/negative/boundary
oracles. A tutorial or a successful parser fixture cannot satisfy that gate.

## OpenTitan requirements that are available

Pin: `7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19`, clean working tree.
The [upstream synthesis collateral](https://github.com/lowRISC/opentitan/blob/7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19/hw/top_earlgrey/syn/chip_earlgrey_asic_nonzero_upf_vals.tcl)
lists bits 3 and 1 of three lifecycle inputs for clamp 1:

- `earlgrey_pd_aon/u_aon_timer/lc_escalate_en_i`
- `earlgrey_pd_main/u_pinmux/lc_escalate_en_i`
- `earlgrey_pd_main/u_pinmux/lc_check_byp_en_i`

The full `top_earlgrey/` paths and original file hash are recorded in
[pilots/opentitan-clamp-inventory.json](pilots/opentitan-clamp-inventory.json).
The [lifecycle package](https://github.com/lowRISC/opentitan/blob/7a3ad34b6d483f4d1d69ac670ddb1c45f1172e19/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv#L62)
encodes Off as four-bit binary `1010`. Consequently a blanket zero clamp does not
encode Off. This does not by itself establish what every consumer does with an
invalid lifecycle encoding. The synthesis file's comment writes `0x1010`; the
actual four-bit enum, rather than that comment's notation, is the encoding source.

The Tcl file is a variable assignment containing requirements, not a complete
power-intent description. The existing checker correctly reports UNSUPPORTED
`set` at line 11, column 1. It must not be made to accept the file as validated
UPF by silently ignoring that command. The inventory replay uses the existing
non-evaluating lexer to inspect only this pinned assignment; it does not execute Tcl.

Unknowns remain: elaborated endpoint existence and bit mapping; drivers and
receiver domains; isolation strategy applicability/precedence; other bit clamps;
control polarity and sequencing; supplies/power states; mapped cell semantics;
and power-aware runtime behavior. Directory/path names are not verified domain
bindings. This source is useful owner-published collateral, but not an approved
complete integration intent or a passing OpenTitan power-aware pilot.

## Replay and evidence

```sh
python3 -m unittest discover -s tests -v
/usr/bin/python3 -m unittest discover -s tests -v
python3 pilots/check_opentitan_clamp_inventory.py "$OPENTITAN_ROOT"
# Inventory replay expects exit 3 (UNKNOWN), not a power qualification pass.
```

The replay checks the clean Git pin, original file SHA-256, exact assignment shape
and all six ordered requirements. It confirms the static checker rejects this
file as unsupported intent. Wrong revisions, dirty inputs and mismatched content
fail with exit 2. Existing 22 tests remain passing on Python 3.9.6 and 3.14.7.
No application RTL, DV, synthesis collateral, parser behavior or CI exclusions
were changed. Raw JSON evidence is retained locally in
`../evidence/upf-collateral/`; the inventory and replay are checked in. This is
collateral provenance and a documented qualification gap, not a semantic release.
