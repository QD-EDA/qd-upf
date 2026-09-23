import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from qd_upf import check, main
from test_qd_upf import VALID, TOPO, run


class EditionTests(unittest.TestCase):
    def audit(self, text):
        return check(text, 'intent.upf', TOPO, 'topology.json', edition='1801-2024')

    def test_legacy_remains_unchanged_and_rejects_marker(self):
        self.assertEqual(run(VALID)['result'], 'ok')
        self.assertNotIn('standard',run(VALID))
        self.assertEqual(run('upf_version 4.0\n'+VALID)['diagnostics'][0]['code'],'UNSUPPORTED')

    def test_declared_version_has_location_and_no_invented_runtime_result(self):
        r=self.audit('# header\nupf_version {4.0}\n'+VALID)
        self.assertEqual(r['result'],'unknown')
        self.assertEqual(r['version_statements'],[{
            'location':'intent.upf:2:1','intended_version':'4.0','runtime_return_value':None}])
        self.assertEqual(r['standard']['edition'],'IEEE 1801-2024')
        self.assertFalse(r['standard']['conformance_established'])
        self.assertEqual(r['crossings'],run(VALID)['crossings'])

    def test_no_marker_query_and_repeated_markers(self):
        for prefix,count in [('',0),('upf_version\n',1),
                             ('upf_version 4.0; upf_version "4.0"\n',2)]:
            r=self.audit(prefix+VALID)
            self.assertEqual(r['result'],'unknown')
            self.assertEqual(len(r['version_statements']),count)
            self.assertTrue(all(v['runtime_return_value'] is None for v in r['version_statements']))

    def test_other_versions_and_bad_arity_stop_before_semantics(self):
        for args,code in [('3.0','UNSUPPORTED_VERSION'),('4','UNSUPPORTED_VERSION'),
                          ('{}','UNSUPPORTED_VERSION'),('5.0','UNSUPPORTED_VERSION'),
                          ('4.0 4.0','BAD_ARGS'),('-help','UNSUPPORTED_VERSION')]:
            r=self.audit('upf_version '+args+'\n'+VALID)
            self.assertEqual(r['result'],'error')
            self.assertEqual(r['domains'],{})
            self.assertEqual(r['diagnostics'][0]['code'],code)

    def test_errors_and_substitutions_are_not_downgraded(self):
        for text in ('upf_version [exec bogus]', 'upf_version $version',
                     'upf_version 4.0\nunsupported_command a'):
            self.assertEqual(self.audit(text)['result'],'error')
        with self.assertRaises(ValueError):
            check(VALID,'i',TOPO,'t',edition='1801-2018')

    def test_cli_unknown_gate_and_metadata_survive_parse_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'i.upf').write_text('upf_version 4.0\n'+VALID)
            (root/'t.json').write_text(json.dumps(TOPO))
            args=['check',str(root/'i.upf'),'--topology',str(root/'t.json'),'--edition','1801-2024','--json']
            out=io.StringIO()
            with contextlib.redirect_stdout(out): self.assertEqual(main(args),3)
            self.assertFalse(json.loads(out.getvalue())['standard']['conformance_established'])
            (root/'i.upf').write_text('upf_version {')
            out=io.StringIO()
            with contextlib.redirect_stdout(out): self.assertEqual(main(args),1)
            self.assertIn('standard',json.loads(out.getvalue()))
