"""CLI and module integration tests; no Docker daemon or network required."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
MOCK_DOCKER = r'''#!/usr/bin/python3
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
with open(os.environ['DOCKER_LOG'], 'a') as log:
    log.write(json.dumps(args) + '\n')
if args[0] == os.environ.get('DOCKER_FAIL'):
    sys.exit(42)
if args[0] == 'run':
    print(os.environ.get('RELEASE_JSON', '{"version":"8.5.11"}'))
elif args[0] == 'create':
    print('test-container')
elif args[0] == 'cp':
    Path(args[2]).write_text('mock binary\n')
'''

MOCK_PYTHON = r'''#!/usr/bin/python3
import json
import os
import sys

record = list(sys.argv)
if '-c' in record:
    sys.exit(1)
record.append(os.environ.get('RUNTIME_DIST', ''))
with open(os.environ['DOCKER_LOG'], 'a') as log:
    log.write(json.dumps(record) + '\n')
if os.environ.get('PYTHON_FAIL') == '1':
    sys.exit(7)
'''


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='musl-build-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project with spaces'
        self.project.mkdir()
        shutil.copy2(PROJECT / 'build-static.sh', self.project)
        for name in ('lib', 'targets', 'tests'):
            shutil.copytree(PROJECT / name, self.project / name)
        self.cwd = self.root / 'output with spaces'
        self.cwd.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        docker = self.bin / 'docker'
        docker.write_text(MOCK_DOCKER)
        docker.chmod(0o755)
        python = self.bin / 'python3'
        python.write_text(MOCK_PYTHON)
        python.chmod(0o755)
        pytest = self.bin / 'pytest'
        pytest.write_text('#!/bin/sh\nexit 0\n')
        pytest.chmod(0o755)
        self.log = self.root / 'docker.log'
        self.env = dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}',
                        DOCKER_LOG=str(self.log))

    def run_build(self, *args, success=True, **env):
        self.log.write_text('')
        result = subprocess.run(
            ['bash', str(self.project / 'build-static.sh'), *args],
            cwd=self.cwd, env=dict(self.env, **env), capture_output=True, text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        self.calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        return result

    def assert_build(self, target, version, alpine='3.20', clean=False, runtime=True):
        builds = [call for call in self.calls if call[0] == 'build']
        self.assertEqual(len(builds), 1)
        build = builds[0]
        self.assertIn(f'VERSION={version}', build)
        self.assertIn(f'ALPINE_VERSION={alpine}', build)
        self.assertEqual('--no-cache' in build, clean)
        self.assertEqual(build[-1], str(self.project / 'targets' / target))
        self.assertEqual(build[build.index('-t') + 1], f'{target}-static-builder')
        output = self.cwd / 'dist' / target
        self.assertEqual(build[build.index('-f') + 1], str(output / 'Dockerfile'))
        self.assertIn(['rm', 'test-container'], self.calls)
        self.assertEqual((output / 'VERSION').read_text(), version + '\n')
        runtime_calls = [call for call in self.calls if str(call[0]).endswith('python3')]
        if runtime:
            self.assertEqual(runtime_calls, [self.calls[-1]])
            call = runtime_calls[0]
            self.assertEqual(call[1:9], [
                '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p',
                f'test_{target}_runtime.py',
            ])
            self.assertEqual(Path(call[-1]).resolve(), (self.cwd / 'dist').resolve())
        else:
            self.assertEqual(runtime_calls, [])
            self.assertEqual(self.calls[-1], ['rm', 'test-container'])
        return output

    def test_help_does_not_build(self):
        for args in ((), ('-h',), ('--help',), ('help',), ('php', '--help')):
            with self.subTest(args=args):
                result = self.run_build(*args)
                self.assertIn('Usage:', result.stdout)
                self.assertIn('php', result.stdout)
                self.assertIn('openssh', result.stdout)
                self.assertIn('curl', result.stdout)
                self.assertIn('wget', result.stdout)
                self.assertIn('apache', result.stdout)
                self.assertIn('rsync', result.stdout)
                self.assertIn('openssl', result.stdout)
                self.assertIn('git', result.stdout)
                self.assertIn('nginx', result.stdout)
                self.assertIn('stunnel', result.stdout)
                self.assertIn('--no-test', result.stdout)
                self.assertEqual(self.calls, [])
                self.assertFalse((self.cwd / 'dist').exists())

    def test_php_default_and_clean(self):
        for args in (('php',), ('php', '8.5'), ('php', '--clean'),
                     ('--clean', 'php')):
            with self.subTest(args=args):
                self.run_build(*args)
                self.assert_build('php', '8.5.11', clean='--clean' in args)
                self.assertEqual(self.calls[0], [
                    'run', '--rm', 'alpine:3.20', 'wget', '-qO-',
                    'https://www.php.net/releases/index.php?json&version=8.5',
                ])

    def test_php_other_series(self):
        self.run_build('php', '8.4', RELEASE_JSON='{ "version" : "8.4.25" }')
        self.assert_build('php', '8.4.25')
        self.assertTrue(self.calls[0][-1].endswith('version=8.4'))

    def test_pinned_php_and_clean(self):
        for args in (('php', '8.5.11'),
                     ('php', '8.5.11', '--clean'), ('--clean', 'php', '8.5.11'),
                     ('php', '--clean', '8.5.11')):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('php', '8.5.11', clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                for name in ('php-cli', 'php-cgi', 'php-fpm'):
                    self.assertTrue((output / name).is_file())
                    self.assertIn(['cp', f'test-container:/out/{name}',
                                   str(output / name)], self.calls)

    def test_php_fpm_is_enabled_and_exported(self):
        self.run_build('php', '8.5.11')
        output = self.assert_build('php', '8.5.11')
        recipe = (output / 'Dockerfile').read_text()
        self.assertIn('\n    --enable-fpm \\\n', recipe)
        self.assertNotIn('--disable-fpm', recipe)
        self.assertIn("file 'sapi/fpm/php-fpm'", recipe)
        self.assertTrue((output / 'php-fpm').is_file())

    def test_openssh_versions(self):
        client = ('ssh', 'scp', 'sftp', 'ssh-keygen', 'ssh-keyscan',
                  'ssh-add', 'ssh-agent', 'sshd', 'sftp-server')
        for args, version, alpine, extra in (
            (('openssh',), '9.9p2', '3.20', ('sshd-session',)),
            (('openssh', '8.9p1', '--clean'), '8.9p1', '3.16', ()),
            (('openssh', '9.3p1'), '9.3p1', '3.20', ()),
            (('--clean', 'openssh', '9.3p1'), '9.3p1', '3.20', ()),
            (('openssh', '10.6p1'), '10.6p1', '3.20', ('sshd-session', 'sshd-auth')),
            (('openssh', '10.0p2'), '10.0p2', '3.20', ('sshd-session', 'sshd-auth')),
        ):
            with self.subTest(args=args):
                output = self.cwd / 'dist' / 'openssh'
                if output.exists():
                    shutil.rmtree(output)
                self.run_build(*args)
                output = self.assert_build('openssh', version, alpine, '--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                names = client + extra
                self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                    ['cp', f'test-container:/out/{name}', str(output / name)]
                    for name in names
                ])
                for name in names:
                    self.assertTrue((output / name).is_file())
                if 'sshd-session' not in extra:
                    self.assertFalse((output / 'sshd-session').exists())
                if 'sshd-auth' not in extra:
                    self.assertFalse((output / 'sshd-auth').exists())

    def test_curl_versions_and_export(self):
        for args, version in (
            (('curl',), '8.22.0'),
            (('curl', '8.10.1', '--clean'), '8.10.1'),
        ):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('curl', version, clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                    ['cp', 'test-container:/out/curl', str(output / 'curl')],
                ])
                self.assertTrue((output / 'curl').is_file())
        result = self.run_build('--list')
        self.assertIn('curl', result.stdout)
        self.assertIn('8.22.0', result.stdout)
        self.assertEqual(self.calls, [])

    def test_wget_versions_and_export(self):
        for args, version in (
            (('wget',), '1.25.0'),
            (('wget', '1.21.4', '--clean'), '1.21.4'),
        ):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('wget', version, clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                    ['cp', 'test-container:/out/wget', str(output / 'wget')],
                ])
                self.assertTrue((output / 'wget').is_file())
        result = self.run_build('--list')
        self.assertIn('wget', result.stdout)
        self.assertIn('1.25.0', result.stdout)
        self.assertEqual(self.calls, [])

    def test_rsync_versions_and_export(self):
        for args, version in (
            (('rsync',), '3.5.1'),
            (('rsync', '3.4.1', '--clean'), '3.4.1'),
        ):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('rsync', version, clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                    ['cp', 'test-container:/out/rsync', str(output / 'rsync')],
                ])
                self.assertTrue((output / 'rsync').is_file())
        result = self.run_build('--list')
        self.assertIn('rsync', result.stdout)
        self.assertIn('3.5.1', result.stdout)
        self.assertEqual(self.calls, [])

    def test_openssl_versions_and_export(self):
        for args, version in (
            (('openssl',), '3.5.9'),
            (('openssl', '3.4.1', '--clean'), '3.4.1'),
        ):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('openssl', version, clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                    ['cp', 'test-container:/out/openssl', str(output / 'openssl')],
                ])
                self.assertTrue((output / 'openssl').is_file())
        result = self.run_build('--list')
        self.assertIn('openssl', result.stdout)
        self.assertIn('3.5.9', result.stdout)
        self.assertEqual(self.calls, [])

    def test_git_versions_and_export(self):
        names = (
            'git',
            'git-receive-pack',
            'git-upload-pack',
            'git-upload-archive',
            'git-shell',
            'git-http-backend',
            'git-remote-http',
            'git-remote-https',
        )
        for args, version in (
            (('git',), '2.56.0'),
            (('git', '2.47.2', '--clean'), '2.47.2'),
        ):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('git', version, clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                self.assertEqual(
                    [call for call in self.calls if call[0] == 'cp'],
                    [['cp', f'test-container:/out/{name}', str(output / name)]
                     for name in names])
                recipe = (output / 'Dockerfile').read_text()
                self.assertIn('build.sh', recipe)
                script = (self.project / 'targets' / 'git' / 'build.sh').read_text()
                self.assertIn('RUNTIME_PREFIX=YesPlease', script)
                self.assertIn('gitexecdir=git', script)
                for name in names:
                    self.assertTrue((output / name).is_file())
        result = self.run_build('--list')
        self.assertIn('git', result.stdout)
        self.assertIn('2.56.0', result.stdout)
        self.assertEqual(self.calls, [])

    def test_apache_versions_and_export(self):
        for args, version in (
            (('apache',), '2.4.69'),
            (('apache', '2.4.62', '--clean'), '2.4.62'),
        ):
            with self.subTest(args=args):
                self.run_build(*args)
                output = self.assert_build('apache', version, clean='--clean' in args)
                self.assertFalse(any(call[0] == 'run' for call in self.calls))
                self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                    ['cp', 'test-container:/out/httpd', str(output / 'httpd')],
                    ['cp', 'test-container:/out/httpd-prefork', str(output / 'httpd-prefork')],
                    ['cp', 'test-container:/out/htpasswd', str(output / 'htpasswd')],
                ])
                recipe = (output / 'Dockerfile').read_text()
                self.assertIn('build-mpms.sh', recipe)
                script = (self.project / 'targets' / 'apache' / 'build-mpms.sh').read_text()
                self.assertIn('build_mpm event httpd', script)
                self.assertIn('build_mpm prefork httpd-prefork', script)
                for name in ('httpd', 'httpd-prefork', 'htpasswd'):
                    self.assertTrue((output / name).is_file())
        result = self.run_build('--list')
        self.assertIn('apache', result.stdout)
        self.assertIn('2.4.69', result.stdout)
        self.assertEqual(self.calls, [])

    def test_nginx_and_stunnel_versions_and_export(self):
        for target, default, pinned in (
            ('nginx', '1.30.6', '1.26.3'),
            ('stunnel', '5.82', '5.77'),
        ):
            for args, version in (((target,), default),
                                  ((target, pinned, '--clean'), pinned)):
                with self.subTest(args=args):
                    self.run_build(*args)
                    output = self.assert_build(target, version, clean='--clean' in args)
                    self.assertFalse(any(call[0] == 'run' for call in self.calls))
                    self.assertEqual([call for call in self.calls if call[0] == 'cp'], [
                        ['cp', f'test-container:/out/{target}', str(output / target)],
                    ])
                    self.assertTrue((output / target).is_file())
            result = self.run_build('--list')
            self.assertIn(target, result.stdout)
            self.assertIn(default, result.stdout)
            self.assertEqual(self.calls, [])

    def test_no_test_records_version_without_checks(self):
        for args, version in (
            (('curl', '--no-test'), '8.22.0'),
            (('--no-test', 'curl', '8.10.1'), '8.10.1'),
            (('curl', '8.10.1', '--no-test'), '8.10.1'),
        ):
            with self.subTest(args=args):
                result = self.run_build(*args)
                self.assert_build('curl', version, runtime=False)
                self.assertIn('Artifact checks were not run (--no-test)', result.stdout)
                self.assertIn('static build OK', result.stdout)

    def test_missing_tools_skip_artifact_checks(self):
        cases = (
            (('docker',), 'python3 and pytest'),
            (('docker', 'python3'), 'pytest'),
            (('docker', 'pytest'), 'python3'),
        )
        for names, missing in cases:
            with self.subTest(missing=missing):
                directory = self.root / ('bin-' + '-'.join(names))
                directory.mkdir()
                for required in ('bash', 'dirname', 'mkdir', 'cat'):
                    (directory / required).symlink_to(shutil.which(required))
                for name in names:
                    tool = directory / name
                    if name == 'docker':
                        tool.write_text(MOCK_DOCKER)
                    elif name == 'python3':
                        tool.write_text(MOCK_PYTHON)
                    else:
                        tool.write_text('#!/bin/sh\nexit 0\n')
                    tool.chmod(0o755)
                result = self.run_build('curl', PATH=str(directory))
                self.assertIn(
                    f'Artifact checks were not run: {missing} not found',
                    result.stdout)
                self.assertIn('static build OK', result.stdout)
                self.assertEqual(
                    (self.cwd / 'dist' / 'curl' / 'VERSION').read_text(),
                    '8.22.0\n')
                self.assertFalse(any(
                    call[1:4] == ['-B', '-m', 'unittest'] for call in self.calls
                    if call))

    def test_runtime_check_failure_fails_the_build(self):
        result = self.run_build('wget', success=False, PYTHON_FAIL='1')
        self.assertIn('Check wget', result.stdout)
        self.assertNotIn('static build OK', result.stdout)
        self.assertTrue(any(str(call[0]).endswith('python3') for call in self.calls))
        self.assertEqual((self.cwd / 'dist' / 'wget' / 'VERSION').read_text(), '1.25.0\n')

    def test_missing_target_shows_help(self):
        self.add_example_target('SHORTHAND_PATTERN="$VERSION_PATTERN"\n')
        for args in (('8.5',), ('8.5.11',), ('8.22.0',), ('1.25.0',),
                     ('9.9p2',), ('10.6p1',), ('10.0p2',), ('2.0.0',),
                     ('2.4.69',), ('3.5.1',), ('3.5.9',), ('2.56.0',),
                     ('--clean',), ('--clean', '1.25.0'), ('8.4', '--clean'),
                     ('--clean', '9.9p2'), ('--no-test',), ('--no-test', '1.25.0'),
                     ('missing',), ('../php',), ('--unknown',), ('clean',)):
            with self.subTest(args=args):
                result = self.run_build(*args)
                self.assertIn('Usage:', result.stdout)
                self.assertEqual(self.calls, [])
                self.assertFalse((self.cwd / 'dist').exists())

    def test_invalid_arguments_fail_before_docker(self):
        for args in (('php', 'clean'), ('php', '8.5.11', 'clean'),
                     ('php', '8.5.bad'), ('openssh', '11.0p1'),
                     ('openssh', '10'), ('openssh', '7.9p1'),
                     ('openssh', '8.5'), ('php', '8.5', '8.4'),
                     ('php', 'openssh'), ('php', '9.9p2'),
                     ('curl', '8.22'), ('curl', '7.88.1'),
                     ('curl', '8.22.0-rc1'), ('curl', '9.9p2'),
                     ('wget', '1.25'), ('wget', '2.3.0'),
                     ('wget', '1.25.0-rc1'), ('wget', '9.9p2'),
                     ('apache', '2.4'), ('apache', '2.2.34'),
                     ('apache', '2.4.69-rc1'), ('apache', '9.9p2'),
                     ('rsync', '3.5'), ('rsync', '2.6.9'),
                     ('rsync', '3.5.1-rc1'), ('rsync', '9.9p2'),
                     ('openssl', '3.5'), ('openssl', '1.1.1w'),
                     ('openssl', '3.5.9-beta1'), ('openssl', '4.0.3'),
                     ('git', '2.56'), ('git', '1.8.5'),
                     ('git', '2.56.0-rc1'), ('git', '9.9p2'),
                     ('nginx', '1.24.0'), ('nginx', '1.25.5'),
                     ('nginx', '1.30'), ('nginx', '2.0.0'),
                     ('nginx', '1.30.6-rc1'), ('stunnel', '5'),
                     ('stunnel', '4.56'), ('stunnel', '5.82.1'),
                     ('stunnel', '5.82;id')):
            with self.subTest(args=args):
                result = self.run_build(*args, success=False)
                self.assertIn('Error:', result.stderr)
                self.assertEqual(self.calls, [])

    def test_release_lookup_errors(self):
        for env in ({'DOCKER_FAIL': 'run'}, {'RELEASE_JSON': '{}'},
                    {'RELEASE_JSON': '{"version":"8.4.25"}'},
                    {'RELEASE_JSON': '{"version":"8.5.bad"}'}):
            with self.subTest(env=env):
                result = self.run_build('php', success=False, **env)
                self.assertIn('Error:', result.stderr)
                self.assertEqual([call[0] for call in self.calls], ['run'])
                self.assertFalse((self.cwd / 'dist').exists())

    def test_docker_failure_and_cleanup(self):
        for action, expected in (
            ('build', ['build']),
            ('create', ['build', 'create']),
            ('cp', ['build', 'create', 'cp', 'rm']),
        ):
            with self.subTest(action=action):
                self.run_build('php', '8.5.11', success=False, DOCKER_FAIL=action)
                self.assertEqual([call[0] for call in self.calls], expected)

    def add_example_target(self, extra=''):
        target = self.project / 'targets' / 'example'
        target.mkdir()
        (target / 'target.sh').write_text('''TARGET_DESCRIPTION="Example tool"
DEFAULT_VERSION="1.2.3"
VERSION_PATTERN='^[0-9]+\\.[0-9]+\\.[0-9]+$'
VERSION_HELP="x.y.z"
ARTIFACTS=("bin/example:example")
''' + extra)
        (target / 'Dockerfile').write_text('''ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION}
ARG VERSION
WORKDIR /usr/src/example-${VERSION}
''')
        return target

    def test_new_target_without_core_changes(self):
        self.add_example_target()
        for flag in ('--list', '--help'):
            result = self.run_build(flag)
            self.assertIn('example', result.stdout)
            self.assertIn('1.2.3', result.stdout)
            self.assertEqual(self.calls, [])
        self.run_build('example')
        output = self.assert_build('example', '1.2.3', runtime=False)
        self.assertTrue((output / 'example').is_file())
        self.run_build('example', '2.0.0', '--clean')
        self.assert_build('example', '2.0.0', clean=True, runtime=False)
        result = self.run_build('2.0.0')
        self.assertIn('Usage:', result.stdout)
        self.assertEqual(self.calls, [])

    def test_invalid_artifacts_fail_before_docker(self):
        target = self.add_example_target()
        original = (target / 'target.sh').read_text()
        for artifact in ('../escape:example', 'bin/example:../escape',
                         'bin/example:bad;name', 'missing-colon'):
            with self.subTest(artifact=artifact):
                (target / 'target.sh').write_text(original + f'ARTIFACTS=("{artifact}")\n')
                self.run_build('example', success=False)
                self.assertEqual(self.calls, [])
        (target / 'target.sh').write_text(original + 'ARTIFACTS=("a:same" "b:same")\n')
        self.run_build('example', success=False)
        self.assertEqual(self.calls, [])

    def test_generated_verification_rejects_each_dynamic_binary(self):
        self.run_build('php', '8.5.11')
        recipe = (self.cwd / 'dist/php/Dockerfile').read_text()
        command = recipe.split('# Shared verification', 1)[1].split('RUN ', 1)[1]
        workspace = self.root / 'verify'
        workspace.mkdir()
        for name in ('sapi/cli/php', 'sapi/cgi/php-cgi', 'sapi/fpm/php-fpm'):
            path = workspace / name
            path.parent.mkdir(parents=True)
            path.write_text('binary placeholder')
        file_tool = self.bin / 'file'
        file_tool.write_text('''#!/bin/sh
if [ "$1" = "$DYNAMIC_BINARY" ]; then
    echo "$1: dynamically linked"
else
    echo "$1: statically linked"
fi
''')
        file_tool.chmod(0o755)
        for dynamic in ('', 'sapi/cli/php', 'sapi/cgi/php-cgi', 'sapi/fpm/php-fpm'):
            with self.subTest(dynamic=dynamic):
                out = workspace / 'out'
                if out.exists():
                    shutil.rmtree(out)
                result = subprocess.run(
                    ['sh', '-c', command.replace('/out', str(out))],
                    cwd=workspace, env=dict(self.env, DYNAMIC_BINARY=dynamic),
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode == 0, not dynamic, result.stderr)
                if not dynamic:
                    self.assertTrue((out / 'php-cli').exists())
                    self.assertTrue((out / 'php-cgi').exists())
                    self.assertTrue((out / 'php-fpm').exists())


if __name__ == '__main__':
    unittest.main()
