"""Frozen QD-UPF v0 cases. Run: python3 -m unittest discover -s tests -v"""
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import qd_upf  # noqa: E402

EX = ROOT / "examples"
VALID = (EX / "valid.upf").read_text()
TOPO = json.loads((EX / "crossings.json").read_text())
HEADER = """\
create_power_domain PD_AON -elements {u_aon}
create_supply_net VDD
create_supply_net VSS
set_domain_supply_net PD_AON -primary_power_net VDD -primary_ground_net VSS
"""


def run(upf, topo=TOPO):
    return qd_upf.check(upf, "t.upf", topo, "t.json")


def codes(report):
    return [(d["code"], d["location"]) for d in report["diagnostics"]]


def cli(*args):
    return subprocess.run([sys.executable, str(ROOT / "qd-upf"), *args],
                          capture_output=True, text=True, cwd=ROOT)


class SpecCases(unittest.TestCase):
    def test_valid_two_domain_with_isolation(self):
        r = run(VALID)
        self.assertEqual(r["result"], "ok", r["diagnostics"])
        self.assertEqual([c["status"] for c in r["crossings"]],
                         ["isolation_declared", "isolation_declared"])
        self.assertEqual(r["crossings"][0]["strategies"], ["PD_CORE/iso_core_out"])

    def test_duplicate_domain(self):
        r = run(VALID + "create_power_domain PD_AON -elements {u_other}\n")
        self.assertEqual(r["result"], "error")
        self.assertIn(("DUPLICATE", "t.upf:21:21"), codes(r))

    def test_unknown_supply(self):
        r = run(VALID.replace("-primary_power_net VDD_AON ", "-primary_power_net VDD_NOPE "))
        self.assertEqual(r["result"], "error")
        self.assertIn(("UNKNOWN_REF", "t.upf:9:50"), codes(r))

    def test_missing_isolation(self):
        r = run((EX / "missing_isolation.upf").read_text())
        self.assertEqual(r["result"], "error")
        self.assertEqual(codes(r), [("MISSING_ISOLATION", "t.json[0]"),
                                    ("MISSING_ISOLATION", "t.json[1]")])
        self.assertEqual(r["crossings"][0]["status"], "missing_isolation")

    def test_tcl_substitution_fails_closed(self):
        cases = {
            "create_power_domain $pd -elements {u_a}\n": "t.upf:1:21",
            "create_power_domain PD -elements [exec touch pwned]\n": "t.upf:1:34",
            'create_power_domain PD -elements "u_$x"\n': "t.upf:1:37",
            "create_power_domain PD -elements u_a\\x41\n": "t.upf:1:37",
            "create_power_domain PD {*}{-elements u_a}\n": "t.upf:1:24",
        }
        for upf, loc in cases.items():
            with self.subTest(upf=upf):
                r = run(upf)
                self.assertEqual(r["result"], "error")
                self.assertEqual(codes(r), [("PARSE", loc)])
        self.assertFalse((ROOT / "pwned").exists())

    def test_braced_multiword_comments_and_continuation(self):
        upf = HEADER + (
            "# a comment; create_power_domain IGNORED -elements {x}\n"
            "create_power_domain PD_CORE \\\n"
            "    -elements {u_core/a {u_core/b} \\\n"
            "               u_core/c[3]} ;# trailing comment\n"
        )
        r = run(upf, [])
        self.assertEqual(r["domains"]["PD_CORE"]["elements"],
                         ["u_core/a", "u_core/b", "u_core/c[3]"])
        self.assertNotIn("IGNORED", r["domains"])


class ExtraChecks(unittest.TestCase):
    def test_unsupported_command_has_location(self):
        r = run(HEADER + "  set_level_shifter ls -domain PD_AON\n")
        self.assertEqual(codes(r), [("UNSUPPORTED", "t.upf:5:3")])

    def test_unknown_option_and_en_dash(self):
        r = run("create_power_domain PD –elements {u_a}\n")
        self.assertEqual(r["result"], "error")
        self.assertEqual(codes(r)[0][0], "BAD_ARGS")

    def test_unclosed_brace_reported_at_open(self):
        r = run("create_power_domain PD -elements {u_a\n")
        self.assertEqual(codes(r), [("PARSE", "t.upf:1:34")])

    def test_extra_chars_after_close_brace(self):
        r = run("create_power_domain PD -elements {u_a}x\n")
        self.assertEqual(codes(r), [("PARSE", "t.upf:1:39")])

    def test_multiply_owned_element(self):
        r = run(VALID + "create_power_domain PD_X -elements {u_core}\n")
        self.assertIn(("MULTI_OWNER", "t.upf:21:36"), codes(r))

    def test_isolation_unknown_element_and_domain(self):
        r = run(VALID + "set_isolation iso2 -domain PD_CORE -elements {u_aon/x}"
                        " -clamp_value 1 -isolation_signal s\n"
                        "set_isolation iso3 -domain PD_NOPE -elements {u_core/x}"
                        " -clamp_value 1 -isolation_signal s\n")
        self.assertEqual(codes(r), [("UNKNOWN_ELEMENT", "t.upf:21:46"),
                                    ("UNKNOWN_REF", "t.upf:22:28")])

    def test_malformed_isolation(self):
        r = run(VALID + "set_isolation iso2 -domain PD_CORE -elements {u_core/x}"
                        " -clamp_value 2\n")
        self.assertEqual(sorted(c for c, _ in codes(r)), ["BAD_ARGS", "BAD_ARGS"])

    def test_missing_primary_supply(self):
        r = run(VALID + "create_power_domain PD_X -elements {u_x}\n")
        self.assertIn(("MISSING_SUPPLY", "t.upf:21:21"), codes(r))

    def test_hierarchy_matches_on_slash_boundary(self):
        topo = [{"name": "c", "source": "PD_CORE", "destination": "PD_AON",
                 "signal": "u_core/irq_extra"}]
        r = run(VALID, topo)
        self.assertEqual(r["crossings"][0]["status"], "missing_isolation")

    def test_topology_without_information_is_unknown(self):
        self.assertEqual(run(VALID, [])["result"], "unknown")
        r = run(VALID, [{"name": "c", "source": "PD_CORE", "destination": "PD_AON"}])
        self.assertEqual(r["result"], "unknown")
        self.assertEqual(codes(r), [("TOPOLOGY_UNKNOWN", "t.json[0]")])

    def test_shared_supply_needs_no_isolation(self):
        upf = HEADER + ("create_power_domain PD_B -elements {u_b}\n"
                        "set_domain_supply_net PD_B -primary_power_net VDD"
                        " -primary_ground_net VSS\n")
        topo = [{"name": "c", "source": "PD_B", "destination": "PD_AON", "signal": "u_b/o"}]
        r = run(upf, topo)
        self.assertEqual(r["result"], "ok")
        self.assertEqual(r["crossings"][0]["status"], "not_required")

    def test_crossing_signal_in_no_domain(self):
        upf = HEADER + ("create_power_domain PD_B -elements {u_b}\n"
                        "set_domain_supply_net PD_B -primary_power_net VDD"
                        " -primary_ground_net VSS\n")
        topo = [{"name": "c", "source": "PD_B", "destination": "PD_AON", "signal": "u_zz/o"}]
        self.assertEqual(codes(run(upf, topo)), [("UNKNOWN_ELEMENT", "t.json[0]")])

    def test_quoted_words(self):
        r = run(HEADER + 'create_power_domain "PD_Q" -elements "u_q1 u_q2"\n', [])
        self.assertEqual(r["domains"]["PD_Q"]["elements"], ["u_q1", "u_q2"])


class Cli(unittest.TestCase):
    def test_exit_codes(self):
        topo = "examples/crossings.json"
        self.assertEqual(cli("check", "examples/valid.upf", "--topology", topo).returncode, 0)
        self.assertEqual(cli("check", "examples/missing_isolation.upf",
                             "--topology", topo).returncode, 1)
        self.assertEqual(cli("check", "examples/valid.upf", "--topology",
                             "examples/empty_topology.json").returncode, 3)

    def test_json_is_deterministic(self):
        args = ("check", "examples/missing_isolation.upf",
                "--topology", "examples/crossings.json", "--json")
        a, b = cli(*args), cli(*args)
        self.assertEqual(a.stdout, b.stdout)
        self.assertEqual(json.loads(a.stdout)["result"], "error")

    def test_bad_topology_json_still_emits_json(self):
        p = cli("check", "examples/valid.upf", "--topology", "tests/bad_topology.json", "--json")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(codes(json.loads(p.stdout)), [("TOPOLOGY", "tests/bad_topology.json")])


if __name__ == "__main__":
    unittest.main()
