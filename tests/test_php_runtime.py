"""Checks for an already built PHP. No Docker build and no network.

Skipped when dist/php/php-cli, dist/php/php-cgi, or dist/php/php-fpm
are absent. The patch version is read from the binaries, because `8.5`
resolves to whatever patch release was current at build time.
"""

import grp
import os
from pathlib import Path
import pwd
import re
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import unittest

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


DIST = runtime_util.artifact_dir('php')
PHP = DIST / 'php-cli'
PHP_CGI = DIST / 'php-cgi'
PHP_FPM = DIST / 'php-fpm'
BINARIES = (PHP, PHP_CGI, PHP_FPM)
VERSION_RE = re.compile(r'PHP ([0-9]+\.[0-9]+\.[0-9]+)')

# Names `php -m` prints for the extensions selected in targets/php/Dockerfile.
RECIPE_MODULES = (
    'bcmath',
    'bz2',
    'calendar',
    'curl',
    'exif',
    'ftp',
    'gd',
    'intl',
    'mbstring',
    'mysqli',
    'mysqlnd',
    'openssl',
    'pcntl',
    'pdo_mysql',
    'pdo_sqlite',
    'sockets',
    'sodium',
    'sqlite3',
    'xml',
    'xsl',
    'zip',
    'zlib',
)

FCGI_BEGIN_REQUEST = 1
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_STDERR = 7
FCGI_RESPONDER = 1


def assert_static(test, binary):
    described = subprocess.run(
        ['file', str(binary)], capture_output=True, text=True, check=True)
    test.assertIn('statically linked', described.stdout)
    linked = subprocess.run(
        ['ldd', str(binary)], capture_output=True, text=True, check=False)
    test.assertIn('not a dynamic executable', linked.stdout + linked.stderr)


def php_version(binary):
    result = subprocess.run(
        [binary, '-v'], capture_output=True, text=True, check=False)
    text = result.stdout + result.stderr
    match = VERSION_RE.search(text)
    if result.returncode != 0 or match is None:
        raise AssertionError(text)
    return match.group(1), text


def unprivileged_account():
    """Return a non-root account php-fpm can drop to, when the system has one."""
    try:
        pwd.getpwnam('nobody')
    except KeyError:
        return None
    for group in ('nogroup', 'nobody'):
        try:
            grp.getgrnam(group)
        except KeyError:
            continue
        return 'nobody', group
    return None


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _name_value(name, value):
    """Encode one FastCGI name/value pair."""
    def length(size):
        if size < 128:
            return bytes((size,))
        return struct.pack('>I', size | 0x80000000)

    raw_name = name.encode()
    raw_value = value.encode()
    return length(len(raw_name)) + length(len(raw_value)) + raw_name + raw_value


def _record(kind, body, request_id=1):
    header = struct.pack('>BBHHBB', 1, kind, request_id, len(body), 0, 0)
    return header + body


def _recv_exact(sock, size):
    chunks = []
    remaining = size
    while remaining:
        piece = sock.recv(remaining)
        if not piece:
            raise ConnectionError('short FastCGI reply')
        chunks.append(piece)
        remaining -= len(piece)
    return b''.join(chunks)


def fcgi_request(port, script, document_root):
    """Send one responder request and return stdout plus stderr bytes."""
    params = {
        'SCRIPT_FILENAME': str(script),
        'SCRIPT_NAME': '/' + script.name,
        'REQUEST_METHOD': 'GET',
        'QUERY_STRING': '',
        'REQUEST_URI': '/' + script.name,
        'DOCUMENT_ROOT': str(document_root),
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'REMOTE_ADDR': '127.0.0.1',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': str(port),
    }
    encoded = b''.join(_name_value(name, value) for name, value in params.items())
    begin = struct.pack('>HBxxxxx', FCGI_RESPONDER, 0)
    payload = b''.join((
        _record(FCGI_BEGIN_REQUEST, begin),
        _record(FCGI_PARAMS, encoded),
        _record(FCGI_PARAMS, b''),
        _record(FCGI_STDIN, b''),
    ))
    with socket.create_connection(('127.0.0.1', port), timeout=5) as sock:
        sock.sendall(payload)
        stdout = b''
        stderr = b''
        while True:
            version, kind, _request, length, padding, _reserved = struct.unpack(
                '>BBHHBB', _recv_exact(sock, 8))
            if version != 1:
                raise AssertionError(f'unexpected FastCGI version {version}')
            body = _recv_exact(sock, length)
            if padding:
                _recv_exact(sock, padding)
            if kind == FCGI_STDOUT:
                stdout += body
            elif kind == FCGI_STDERR:
                stderr += body
            elif kind == FCGI_END_REQUEST:
                return stdout, stderr


@unittest.skipUnless(all(binary.is_file() for binary in BINARIES),
                      'dist/php binaries are not built')
class PHPRuntimeTests(unittest.TestCase):
    def test_sapis_are_statically_linked(self):
        for binary in BINARIES:
            with self.subTest(binary=binary.name):
                assert_static(self, binary)

    def test_sapis_report_the_same_release(self):
        versions = {}
        texts = {}
        for binary in BINARIES:
            versions[binary.name], texts[binary.name] = php_version(binary)
        self.assertEqual(len(set(versions.values())), 1, versions)
        self.assertIn('(cli)', texts['php-cli'])
        self.assertIn('(cgi-fcgi)', texts['php-cgi'])
        self.assertIn('(fpm-fcgi)', texts['php-fpm'])

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('php')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        for binary in BINARIES:
            with self.subTest(binary=binary.name):
                version, _text = php_version(binary)
                self.assertEqual(version, expected)

    def test_recipe_modules_are_compiled_in(self):
        result = subprocess.run(
            [PHP, '-m'], capture_output=True, text=True, check=True)
        modules = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        missing = [name for name in RECIPE_MODULES if name not in modules]
        self.assertEqual(missing, [], result.stdout)

    def test_fpm_answers_one_request(self):
        account = None
        if os.geteuid() == 0:
            account = unprivileged_account()
            if account is None:
                self.skipTest('serving a FastCGI request as root needs a nobody account')
        root = Path(tempfile.mkdtemp(prefix='php-fpm-runtime-'))
        self.addCleanup(shutil.rmtree, root, True)
        script = root / 'index.php'
        script.write_text(
            '<?php\n'
            'echo "hello-fpm\\n";\n'
            'foreach (get_loaded_extensions() as $name) {\n'
            '    echo strtolower($name), "\\n";\n'
            '}\n'
        )
        port = free_port()
        user_lines = ''
        if account is not None:
            user, group = account
            user_lines = f'user = {user}\ngroup = {group}\n'
            root.chmod(0o755)
            script.chmod(0o644)
        config = root / 'php-fpm.conf'
        config.write_text(
            '[global]\n'
            f'error_log = {root / "error.log"}\n'
            f'pid = {root / "php-fpm.pid"}\n'
            '\n'
            '[www]\n'
            f'{user_lines}'
            f'listen = 127.0.0.1:{port}\n'
            'pm = static\n'
            'pm.max_children = 1\n'
        )
        output = root / 'stdout'
        with output.open('w') as stream:
            process = subprocess.Popen(
                [PHP_FPM, '-n', '-y', str(config), '-F'],
                stdout=stream, stderr=subprocess.STDOUT)
        self.addCleanup(self.stop_fpm, process)

        stdout = stderr = None
        for _ in range(50):
            if process.poll() is not None:
                break
            try:
                stdout, stderr = fcgi_request(port, script, root)
                break
            except (ConnectionError, socket.timeout, TimeoutError, OSError):
                time.sleep(0.1)
        details = output.read_text()
        log = root / 'error.log'
        if log.is_file():
            details += log.read_text()
        self.assertIsNotNone(stdout, details)
        text = stdout.decode()
        self.assertIn('hello-fpm', text, details + (stderr or b'').decode(errors='replace'))
        found = {line.strip() for line in text.lower().splitlines() if line.strip()}
        missing = [name for name in RECIPE_MODULES if name not in found]
        self.assertEqual(missing, [], text)

    @staticmethod
    def stop_fpm(process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
