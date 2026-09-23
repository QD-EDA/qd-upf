# Supply-net list correction

Normative anchor: user-supplied IEEE 1801-2024 §6.25 (syntax) and §6.25.1,
printed p.151 / PDF p.152. The positional argument is a list; creation applies
to each unique name in that list. The licensed document identity is recorded in
IEEE1801_2024_REVIEW.md; neither the PDF nor extracted text is distributed here.

Previously `create_supply_net {VDD VSS}` stored a single name containing a space,
so subsequent references to VDD and VSS failed. The correction uses the existing
bounded list parser during argument validation, preserves first-occurrence order,
and creates each unique name once. An unknown domain prevents all names in that
command from being created. Existing single-name behavior and 22 tests remain.
Duplicates across separate commands still report the dialect's existing error.

Six added tests cover equivalent grouped/separate declarations, repeated names
within one list, nested singleton braces, outer quoted lists, cross-command
duplicates, empty/whitespace names, unsupported inner quoted elements, and an
unknown domain. A separate Tcl 9.0.4 interpreter agrees on six supported list
forms, including bracketed bus names and newline separators. The oracle receives
hex-encoded data and runs only a fixed list-reading script, never UPF/Tcl source
from an input design. It validates list tokenization, not UPF supply semantics.
The Tcl oracle explicitly skips if unavailable; the five other tests still run.

```sh
python3 -m unittest discover -s tests -v
/usr/bin/python3 -m unittest discover -s tests -v
printf 'puts [info patchlevel]\n' | tclsh
```

All 28 tests pass on Python 3.14.7 and Apple Python 3.9.6 with Tcl 9.0.4 on macOS.
Initial new tests failed on the old implementation. One test setup initially
included unrelated default crossings and was corrected to use an empty topology
for its isolated unknown-domain case. No existing test was altered or weakened.
Logs are local under `../evidence/upf-supply-lists/`.

This is one clause-backed parser correction in the bounded dialect, not an
IEEE 1801-2024 mode or conformance claim. General Tcl lists, identifier/scope
resolution, available supply sets, reuse, net resolution, supply transitions,
isolation implementation and Icarus/UVM runtime remain unverified. No real-design
power-aware pilot or independent UPF engine result is established by this change.
