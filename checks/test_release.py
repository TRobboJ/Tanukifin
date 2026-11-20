import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

spec = importlib.util.spec_from_file_location('release', Path(__file__).resolve().parents[1] / 'scripts/release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseGuards(unittest.TestCase):
    def setUp(self):
        self.version = (release.ROOT / 'VERSION').read_text().strip()
        self.env = patch.dict(os.environ, REQUESTED_VERSION=self.version,
                              GITHUB_REF='refs/heads/main', GITHUB_SHA='a' * 40,
                              GITHUB_REPOSITORY='example/test', GH_TOKEN='test-token')
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_exact_version(self):
        self.assertEqual(release.version(), self.version)

    def test_mismatched_or_injected_version(self):
        for version in ['0.0.0', '1.2.0; echo injected', 'v' + self.version, '$(id)']:
            os.environ['REQUESTED_VERSION'] = version
            with self.assertRaises(ValueError):
                release.version()

    def test_non_main_rejected(self):
        os.environ['GITHUB_REF'] = 'refs/heads/topic'
        with self.assertRaises(ValueError):
            release.version()

    def test_existing_tag_rejected(self):
        with patch.object(release.urllib.request, 'urlopen'):
            with self.assertRaises(ValueError):
                release.check()

    def test_only_not_found_is_accepted(self):
        for status in [401, 403, 429, 500]:
            error = urllib.error.HTTPError('https://api.github.com/', status, 'error', {}, None)
            with patch.object(release.urllib.request, 'urlopen', side_effect=error):
                with self.assertRaises(urllib.error.HTTPError):
                    release.check()
        error = urllib.error.HTTPError('https://api.github.com/', 404, 'missing', {}, None)
        with patch.object(release.urllib.request, 'urlopen', side_effect=error) as fetch:
            self.assertEqual(release.check(), self.version)
            self.assertEqual(fetch.call_count, 2)


if __name__ == '__main__':
    unittest.main()
