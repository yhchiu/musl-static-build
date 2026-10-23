"""Checks for an already built curl. No Docker build and no network.

Skipped when dist/curl/curl is absent.
"""

import subprocess
import unittest

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


CURL = runtime_util.artifact_dir('curl') / 'curl'


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


@unittest.skipUnless(CURL.is_file(), 'dist/curl/curl is not built')
class CurlRuntimeTests(unittest.TestCase):
    def test_curl_is_statically_linked(self):
        assert_static(self, CURL)

    def test_https_and_http2(self):
        result = subprocess.run(
            [CURL, '--version'], capture_output=True, text=True, check=True)
        text = result.stdout
        protocols = []
        features = []
        for line in text.splitlines():
            if line.startswith('Protocols:'):
                protocols = line.split(':', 1)[1].split()
            elif line.startswith('Features:'):
                features = line.split(':', 1)[1].split()
        self.assertIn('https', protocols)
        self.assertIn('HTTP2', features)

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('curl')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        result = subprocess.run(
            [CURL, '--version'], capture_output=True, text=True, check=True)
        self.assertIn(f'curl {expected} ', result.stdout)


if __name__ == '__main__':
    unittest.main()
