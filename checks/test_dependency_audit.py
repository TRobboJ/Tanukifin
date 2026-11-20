import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location('audit', Path(__file__).resolve().parents[1] / 'scripts/audit_dependencies.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AdvisoryGate(unittest.TestCase):
    def run_audit(self, result):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'audit.json'
            with patch.object(audit, 'declared', return_value={('example:library', '1.0.0')}), \
                 patch.object(audit.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(result).encode())):
                audit.audit(Path(directory), output)
                return json.loads(output.read_text())

    def test_advisory_blocks_build(self):
        with self.assertRaises(SystemExit):
            self.run_audit({'results': [{'vulns': [{'id': 'SYNTHETIC-ADVISORY'}]}]})

    def test_incomplete_or_error_response_blocks_build(self):
        for result in [{'results': []}, {'results': [{'next_page_token': 'more'}]},
                       {'results': [{'error': {'code': 500}}]}]:
            with self.assertRaises(ValueError):
                self.run_audit(result)

    def test_empty_advisory_list_records_checked_packages(self):
        report = self.run_audit({'results': [{}]})
        self.assertEqual(report['findings'], [])
        self.assertEqual(report['packages'], [{'name': 'example:library', 'version': '1.0.0'}])

    def test_network_failure_does_not_pass(self):
        with patch.object(audit, 'declared', return_value={('example:library', '1.0.0')}), \
             patch.object(audit.urllib.request, 'urlopen', side_effect=urllib.error.URLError('offline')):
            with self.assertRaises(urllib.error.URLError):
                audit.audit(Path('.'), Path('unused.json'))


if __name__ == '__main__':
    unittest.main()
