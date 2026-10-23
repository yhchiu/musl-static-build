"""Checks for an already built rsync. No Docker build and no network.

Skipped when dist/rsync/rsync is absent.
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


RSYNC = runtime_util.artifact_dir('rsync') / 'rsync'


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


@unittest.skipUnless(RSYNC.is_file(), 'dist/rsync/rsync is not built')
class RsyncRuntimeTests(unittest.TestCase):
    def test_rsync_is_statically_linked(self):
        assert_static(self, RSYNC)

    def test_compression_and_checksums(self):
        result = subprocess.run(
            [RSYNC, '--version'], capture_output=True, text=True, check=True)
        text = result.stdout
        self.assertIn('xxhash', text)
        self.assertIn('zstd', text)
        self.assertIn('lz4', text)
        self.assertIn('zlib', text)
        self.assertIn('openssl', text)

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('rsync')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        result = subprocess.run(
            [RSYNC, '--version'], capture_output=True, text=True, check=True)
        self.assertIn(f'rsync  version {expected} ', result.stdout)

    def test_copies_a_local_file(self):
        root = Path(tempfile.mkdtemp(prefix='rsync-runtime-'))
        self.addCleanup(shutil.rmtree, root, True)
        source = root / 'source'
        dest = root / 'dest'
        source.mkdir()
        dest.mkdir()
        (source / 'hello.txt').write_text('hello-rsync')
        result = subprocess.run(
            [RSYNC, '-a', f'{source}/', str(dest)],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((dest / 'hello.txt').read_text(), 'hello-rsync')


if __name__ == '__main__':
    unittest.main()
