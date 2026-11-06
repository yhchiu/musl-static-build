"""Build provenance checks with a fake Docker CLI (no daemon required)."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
DOCKER_MOCK = r'''#!/usr/bin/python3
import json
import os
from pathlib import Path
import sys
args = sys.argv[1:]
with open(os.environ['DOCKER_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\n')
if args[0] == os.environ.get('DOCKER_FAIL'):
    sys.exit(42)
if args[:2] == ['image', 'inspect']:
    if 'RepoDigests' in args[3]:
        print(os.environ.get('IMAGE_REF', 'alpine@sha256:' + 'a' * 64))
    else:
        print(os.environ.get('IMAGE_PLATFORM', 'linux/amd64'))
elif args[0] == 'create':
    print('test-container')
elif args[0] == 'cp':
    if args[1].endswith('/APK-PACKAGES.txt'):
        Path(args[2]).write_text('musl-1.2.5-r0\nopenssl-3.3.0-r0\n')
    else:
        Path(args[2]).write_bytes(b'example binary contents\n')
'''


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='musl-provenance-')
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.project = root / 'project'
        (self.project / 'lib').mkdir(parents=True)
        (self.project / 'targets' / 'example').mkdir(parents=True)
        shutil.copy2(PROJECT / 'build-static.sh', self.project)
        shutil.copy2(PROJECT / 'lib' / 'build.sh', self.project / 'lib')
        (self.project / 'targets' / 'example' / 'target.sh').write_text('''
TARGET_DESCRIPTION="Example"
DEFAULT_VERSION="9.9p2"
VERSION_PATTERN='^([89]\\.[0-9]+p[0-9]+)$'
VERSION_HELP="8.x or 9.x"
ARTIFACTS=("ssh:ssh" "sshd:sshd")
target_prepare() {
    if [[ "$VERSION" == 8.* ]]; then ALPINE_VERSION="3.16"; fi
}
''')
        (self.project / 'targets' / 'example' / 'Dockerfile').write_text(
            'ARG ALPINE_VERSION=3.20\nFROM alpine:${ALPINE_VERSION} AS builder\n'
        )
        self.cwd = root / 'output with spaces'
        self.cwd.mkdir()
        self.output = self.cwd / 'dist' / 'example'
        self.bin = root / 'bin'
        self.bin.mkdir()
        (self.bin / 'docker').write_text(DOCKER_MOCK)
        (self.bin / 'docker').chmod(0o755)
        self.log = root / 'docker.log'
        self.env = dict(os.environ, DOCKER_LOG=str(self.log),
                        PATH=f'{self.bin}:{os.environ["PATH"]}')

    def run_build(self, *args, success=True, **env):
        self.log.write_text('')
        result = subprocess.run(
            ['bash', str(self.project / 'build-static.sh'), 'example', *args],
            cwd=self.cwd, env=dict(self.env, **env),
            capture_output=True, text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result

    def test_digest_is_used_and_recorded(self):
        self.run_build()
        self.assertIn(['pull', 'alpine:3.20'], self.calls)
        build = next(call for call in self.calls if call[0] == 'build')
        self.assertIn('ALPINE_VERSION=3.20@sha256:' + 'a' * 64, build)
        self.assertEqual(build[build.index('--platform') + 1], 'linux/amd64')
        info = (self.output / 'BUILD-INFO.txt').read_text()
        self.assertIn('BASE_IMAGE_REF=alpine:3.20@sha256:' + 'a' * 64, info)
        self.assertIn('BASE_IMAGE_REPO_DIGEST=alpine@sha256:' + 'a' * 64, info)
        self.assertIn('BASE_PLATFORM=linux/amd64\n', info)
        self.assertIn('BUILD_NO_CACHE=false\n', info)
        self.assertIn('GIT_COMMIT=unknown\n', info)
        self.assertEqual((self.output / 'APK-PACKAGES.txt').read_text(),
                         'musl-1.2.5-r0\nopenssl-3.3.0-r0\n')
        generated = (self.output / 'Dockerfile').read_text()
        self.assertIn('apk info -v > /out/APK-PACKAGES.txt', generated)
        self.assertIn('statically linked', generated)
        self.assertEqual(subprocess.run(
            ['sha256sum', '-c', 'SHA256SUMS'], cwd=self.output,
            capture_output=True).returncode, 0)
        (self.output / 'ssh').write_text('tampered\n')
        self.assertNotEqual(subprocess.run(
            ['sha256sum', '-c', 'SHA256SUMS'], cwd=self.output,
            capture_output=True).returncode, 0)

    def test_target_preparation_chooses_alpine_316(self):
        self.run_build('8.9p1', '--clean')
        self.assertIn(['pull', 'alpine:3.16'], self.calls)
        build = next(call for call in self.calls if call[0] == 'build')
        self.assertIn('--no-cache', build)
        self.assertIn('ALPINE_VERSION=3.16@sha256:' + 'a' * 64, build)
        info = (self.output / 'BUILD-INFO.txt').read_text()
        self.assertIn('BASE_IMAGE_TAG=alpine:3.16\n', info)
        self.assertIn('BUILD_NO_CACHE=true\n', info)

    def test_qualified_repo_digest_and_arm_platform(self):
        self.run_build(IMAGE_REF='docker.io/library/alpine@sha256:' + 'b' * 64,
                       IMAGE_PLATFORM='linux/arm64/v8')
        build = next(call for call in self.calls if call[0] == 'build')
        self.assertIn('ALPINE_VERSION=3.20@sha256:' + 'b' * 64, build)
        self.assertEqual(build[build.index('--platform') + 1], 'linux/arm64/v8')
        info = (self.output / 'BUILD-INFO.txt').read_text()
        self.assertIn('BASE_PLATFORM=linux/arm64/v8\n', info)

    def test_invalid_digest_fails_without_build(self):
        result = self.run_build(success=False, IMAGE_REF='alpine@sha256:bad')
        self.assertIn('cannot resolve Alpine image digest', result.stderr)
        self.assertFalse(any(c[0] == 'build' for c in self.calls))
        self.assertFalse((self.output / 'BUILD-INFO.txt').exists())

    def test_failed_rebuild_removes_prior_metadata(self):
        self.run_build()
        self.assertTrue((self.output / 'SHA256SUMS').exists())
        self.assertTrue((self.output / 'VERSION').exists())
        self.run_build(success=False, DOCKER_FAIL='pull')
        for filename in ('BUILD-INFO.txt', 'APK-PACKAGES.txt', 'SHA256SUMS', 'VERSION'):
            self.assertFalse((self.output / filename).exists(), filename)
        self.assertTrue((self.output / 'ssh').exists())  # Older binaries are untouched.

    def test_package_copy_failure_does_not_publish_provenance(self):
        self.run_build(success=False, DOCKER_FAIL='cp')
        self.assertEqual(self.calls[-1], ['rm', 'test-container'])
        self.assertFalse((self.output / 'BUILD-INFO.txt').exists())


if __name__ == '__main__':
    unittest.main()
