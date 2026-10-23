"""Checks for an already built OpenSSH. No Docker build and no network.

Skipped when dist/openssh/ssh is absent. sshd-session and sshd-auth are
required only for the versions that actually ship them.
"""

import re
import subprocess
import unittest

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


DIST = runtime_util.artifact_dir('openssh')
SSH = DIST / 'ssh'

ALWAYS = (
    'ssh', 'scp', 'sftp', 'ssh-keygen', 'ssh-keyscan',
    'ssh-add', 'ssh-agent', 'sshd', 'sftp-server',
)
VERSION_RE = re.compile(r'OpenSSH_([0-9]+)\.([0-9]+)p([0-9]+)')


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


def openssh_version(binary):
    result = subprocess.run(
        [binary, '-V'], capture_output=True, text=True, check=False)
    text = result.stdout + result.stderr
    match = VERSION_RE.search(text)
    if result.returncode != 0 or match is None:
        raise AssertionError(text)
    return tuple(int(part) for part in match.groups()), match.group(0)


def expected_names(version):
    major, minor, _patch = version
    names = list(ALWAYS)
    # 9.8 split the listener from sshd-session. 10.0 added sshd-auth.
    if major > 9 or (major == 9 and minor >= 8):
        names.append('sshd-session')
    if major >= 10:
        names.append('sshd-auth')
    return names


@unittest.skipUnless(SSH.is_file(), 'dist/openssh/ssh is not built')
class OpenSSHRuntimeTests(unittest.TestCase):
    def test_version_selects_server_binaries(self):
        version, label = openssh_version(SSH)
        sshd_version, sshd_label = openssh_version(DIST / 'sshd')
        self.assertEqual(sshd_version, version)
        self.assertEqual(sshd_label, label)

        expected = expected_names(version)
        for name in expected:
            binary = DIST / name
            with self.subTest(binary=name):
                self.assertTrue(binary.is_file(), f'missing {name}')
                assert_static(self, binary)
        for name in ('sshd-session', 'sshd-auth'):
            if name not in expected:
                self.assertFalse((DIST / name).exists(), name)

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('openssh')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        _version, label = openssh_version(SSH)
        self.assertEqual(label, f'OpenSSH_{expected}')


if __name__ == '__main__':
    unittest.main()
