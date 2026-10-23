"""Checks for an already built wget. No Docker build and no network.

Skipped when dist/wget/wget is absent.
"""

import subprocess
import unittest

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


WGET = runtime_util.artifact_dir('wget') / 'wget'


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


@unittest.skipUnless(WGET.is_file(), 'dist/wget/wget is not built')
class WgetRuntimeTests(unittest.TestCase):
    def test_wget_is_statically_linked(self):
        assert_static(self, WGET)

    def test_https_zlib_and_pcre2(self):
        result = subprocess.run(
            [WGET, '--version'], capture_output=True, text=True, check=True)
        text = result.stdout
        self.assertIn('+https', text)
        self.assertIn('+ssl/openssl', text)
        # The link line names the libraries. It does not pin their versions.
        self.assertIn('-lpcre2-8', text)
        self.assertIn(' -lz ', text)

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('wget')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        result = subprocess.run(
            [WGET, '--version'], capture_output=True, text=True, check=True)
        self.assertIn(f'GNU Wget {expected} ', result.stdout)


if __name__ == '__main__':
    unittest.main()
