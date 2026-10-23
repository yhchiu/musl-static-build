"""Checks for an already built openssl command. No Docker build and no network.

Skipped when dist/openssl/openssl is absent.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


OPENSSL = runtime_util.artifact_dir('openssl') / 'openssl'


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


@unittest.skipUnless(OPENSSL.is_file(), 'dist/openssl/openssl is not built')
class OpenSSLRuntimeTests(unittest.TestCase):
    def test_openssl_is_statically_linked(self):
        assert_static(self, OPENSSL)

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('openssl')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        result = subprocess.run(
            [OPENSSL, 'version'], capture_output=True, text=True, check=True)
        self.assertIn(f'OpenSSL {expected}', result.stdout)

    def test_creates_a_certificate(self):
        root = Path(tempfile.mkdtemp(prefix='openssl-runtime-'))
        self.addCleanup(shutil.rmtree, root, True)
        key = root / 'key.pem'
        cert = root / 'cert.pem'
        created = subprocess.run(
            [OPENSSL, 'req', '-x509', '-newkey', 'rsa:2048',
             '-keyout', str(key), '-out', str(cert),
             '-days', '1', '-nodes', '-subj', '/CN=localhost'],
            capture_output=True, text=True, check=False)
        self.assertEqual(created.returncode, 0, created.stderr)
        shown = subprocess.run(
            [OPENSSL, 'x509', '-in', str(cert), '-noout', '-subject'],
            capture_output=True, text=True, check=True)
        self.assertIn('localhost', shown.stdout)


if __name__ == '__main__':
    unittest.main()
