"""Checks for an already built git. No Docker build and no network.

Skipped when dist/git/git is absent.
"""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


GIT_DIR = runtime_util.artifact_dir('git')
GIT = GIT_DIR / 'git'
HELPERS = (
    'git-receive-pack',
    'git-upload-pack',
    'git-upload-archive',
    'git-shell',
    'git-http-backend',
    'git-remote-http',
    'git-remote-https',
)


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


@unittest.skipUnless(GIT.is_file(), 'dist/git/git is not built')
class GitRuntimeTests(unittest.TestCase):
    def test_exported_binaries_are_statically_linked(self):
        assert_static(self, GIT)
        for name in HELPERS:
            with self.subTest(name=name):
                binary = GIT_DIR / name
                self.assertTrue(binary.is_file(), name)
                assert_static(self, binary)

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('git')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        result = subprocess.run(
            [GIT, '--version'], capture_output=True, text=True, check=True)
        self.assertIn(f'git version {expected}', result.stdout)

    def test_exec_path_is_the_directory_of_the_binary(self):
        git = GIT.resolve()
        result = subprocess.run(
            [git, '--exec-path'], capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), str(git.parent))

    def test_init_and_commit_without_templates(self):
        root = Path(tempfile.mkdtemp(prefix='git-runtime-'))
        self.addCleanup(shutil.rmtree, root, True)
        env = os.environ.copy()
        env.update({
            'HOME': str(root),
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_AUTHOR_NAME': 'Test',
            'GIT_AUTHOR_EMAIL': 'test@example.com',
            'GIT_COMMITTER_NAME': 'Test',
            'GIT_COMMITTER_EMAIL': 'test@example.com',
        })
        created = subprocess.run(
            [GIT, 'init'], cwd=root, env=env,
            capture_output=True, text=True, check=False)
        self.assertEqual(created.returncode, 0, created.stderr)
        self.assertFalse((root / '.git' / 'hooks' / 'pre-commit.sample').exists())
        (root / 'hello.txt').write_text('hello-git')
        added = subprocess.run(
            [GIT, 'add', 'hello.txt'], cwd=root, env=env,
            capture_output=True, text=True, check=False)
        self.assertEqual(added.returncode, 0, added.stderr)
        committed = subprocess.run(
            [GIT, 'commit', '-m', 'hello'], cwd=root, env=env,
            capture_output=True, text=True, check=False)
        self.assertEqual(committed.returncode, 0, committed.stderr)
        shown = subprocess.run(
            [GIT, 'log', '-1', '--format=%s'], cwd=root, env=env,
            capture_output=True, text=True, check=True)
        self.assertEqual(shown.stdout.strip(), 'hello')


if __name__ == '__main__':
    unittest.main()
