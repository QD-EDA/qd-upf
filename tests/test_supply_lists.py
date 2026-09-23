import unittest
from test_qd_upf import run, VALID


class SupplyListTests(unittest.TestCase):
    def test_list_equivalent_to_separate_declarations(self):
        grouped = VALID.replace('create_supply_net VDD_AON     -domain PD_AON\ncreate_supply_net VSS         -domain PD_AON',
                                'create_supply_net {VDD_AON VSS VDD_AON} -domain PD_AON')
        report = run(grouped)
        self.assertEqual(report['result'], 'ok', report['diagnostics'])
        self.assertEqual(report['crossings'], run(VALID)['crossings'])

    def test_quoted_and_nested_singleton_lists(self):
        for value in ('"VDD_AON VSS"', '{{VDD_AON} {VSS}}'):
            grouped = VALID.replace('create_supply_net VDD_AON     -domain PD_AON\ncreate_supply_net VSS         -domain PD_AON',
                                    'create_supply_net '+value+' -domain PD_AON')
            self.assertEqual(run(grouped)['result'], 'ok')

    def test_duplicate_across_commands_still_errors(self):
        report = run(VALID + 'create_supply_net {VDD_AON NEW_NET}\n')
        self.assertEqual(report['result'], 'error')
        self.assertTrue(any(d['code']=='DUPLICATE' and "'VDD_AON'" in d['message'] for d in report['diagnostics']))

    def test_empty_or_unsupported_list_fails_before_semantics(self):
        for value in ('{}', '{ }', '{{}}', '{{ }}', '{VDD {}}', '{VDD "VSS"}'):
            report = run('create_supply_net '+value+'\n')
            self.assertEqual(report['result'], 'error')
            self.assertEqual(report['domains'], {})
            self.assertTrue(all(d['code']=='BAD_ARGS' for d in report['diagnostics']))

    def test_domain_reference_checked_for_list(self):
        report = run('create_supply_net {VDD VSS} -domain MISSING\n', [])
        self.assertEqual(report['result'], 'error')
        self.assertEqual(len(report['diagnostics']), 1)
        self.assertEqual(report['diagnostics'][0]['code'], 'UNKNOWN_REF')

    def test_supported_list_syntax_matches_installed_tcl(self):
        import shutil
        import subprocess
        from qd_upf import split_list
        executable = shutil.which('tclsh')
        if not executable:
            self.skipTest('Tcl list oracle is not installed')
        for value in ('VDD', 'VDD VSS', '{VDD} {VSS}', 'VDD VSS VDD', ' VDD\nVSS ', 'VDD[0] VDD[1]'):
            # Data enters as hex, never as Tcl source; no UPF command is evaluated.
            script = ('set value [encoding convertfrom utf-8 [binary decode hex '+value.encode().hex()+']]\n'
                      'foreach item $value {puts [binary encode hex [encoding convertto utf-8 $item]]}\n')
            result = subprocess.run([executable], input=script, text=True, capture_output=True, check=True)
            self.assertFalse(result.stderr)
            actual = [bytes.fromhex(line).decode() for line in result.stdout.splitlines()]
            self.assertEqual(split_list(value), actual)
