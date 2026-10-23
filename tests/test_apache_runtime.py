"""Checks for an already built Apache httpd. No Docker build and no network.

Skipped when dist/apache/httpd, dist/apache/httpd-prefork, or
dist/apache/htpasswd are absent.
"""

import grp
import os
from pathlib import Path
import pwd
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request

try:
    import runtime_util
except ImportError:  # loaded as tests.test_* from the project root
    from tests import runtime_util


PROJECT = Path(__file__).resolve().parents[1]
DIST = runtime_util.artifact_dir('apache')
HTTPD = DIST / 'httpd'
HTTPD_PREFORK = DIST / 'httpd-prefork'
HTPASSWD = DIST / 'htpasswd'
SERVERS = (HTTPD, HTTPD_PREFORK)

# Checked-in list from `httpd -l` for the verified 2.4.69 event build.
# prefork uses the same modules with event/mod_cgid swapped.
COMPILED_MODULES = (
    'core',
    'mod_authn_file',
    'mod_authn_dbm',
    'mod_authn_anon',
    'mod_authn_dbd',
    'mod_authn_socache',
    'mod_authn_core',
    'mod_authz_host',
    'mod_authz_groupfile',
    'mod_authz_user',
    'mod_authz_dbm',
    'mod_authz_owner',
    'mod_authz_dbd',
    'mod_authz_core',
    'mod_access_compat',
    'mod_auth_basic',
    'mod_auth_form',
    'mod_auth_digest',
    'mod_allowmethods',
    'mod_file_cache',
    'mod_cache',
    'mod_cache_disk',
    'mod_cache_socache',
    'mod_socache_shmcb',
    'mod_socache_dbm',
    'mod_socache_memcache',
    'mod_socache_redis',
    'mod_watchdog',
    'mod_macro',
    'mod_dbd',
    'mod_dumpio',
    'mod_buffer',
    'mod_ratelimit',
    'mod_reqtimeout',
    'mod_ext_filter',
    'mod_request',
    'mod_include',
    'mod_filter',
    'mod_substitute',
    'mod_sed',
    'mod_deflate',
    'mod_brotli',
    'http_core',
    'mod_mime',
    'mod_log_config',
    'mod_log_debug',
    'mod_logio',
    'mod_env',
    'mod_expires',
    'mod_headers',
    'mod_unique_id',
    'mod_setenvif',
    'mod_version',
    'mod_remoteip',
    'mod_proxy',
    'mod_proxy_connect',
    'mod_proxy_ftp',
    'mod_proxy_http',
    'mod_proxy_fcgi',
    'mod_proxy_scgi',
    'mod_proxy_uwsgi',
    'mod_proxy_fdpass',
    'mod_proxy_wstunnel',
    'mod_proxy_ajp',
    'mod_proxy_balancer',
    'mod_proxy_express',
    'mod_proxy_hcheck',
    'mod_session',
    'mod_session_cookie',
    'mod_session_dbd',
    'mod_slotmem_shm',
    'mod_ssl',
    'mod_http2',
    'mod_proxy_http2',
    'mod_lbmethod_byrequests',
    'mod_lbmethod_bytraffic',
    'mod_lbmethod_bybusyness',
    'mod_lbmethod_heartbeat',
    'event',
    'mod_unixd',
    'mod_heartbeat',
    'mod_heartmonitor',
    'mod_dav',
    'mod_status',
    'mod_autoindex',
    'mod_info',
    'mod_cgid',
    'mod_dav_fs',
    'mod_dav_lock',
    'mod_vhost_alias',
    'mod_negotiation',
    'mod_dir',
    'mod_actions',
    'mod_speling',
    'mod_userdir',
    'mod_alias',
    'mod_rewrite',
)
PREFORK_MODULES = tuple(
    {'event': 'prefork', 'mod_cgid': 'mod_cgi'}.get(name, name)
    for name in COMPILED_MODULES
)


def compiled_modules(binary):
    result = subprocess.run([binary, '-l'], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    modules = []
    for line in result.stdout.splitlines():
        name = line.strip()
        if name.endswith('.c'):
            modules.append(name[:-2])
    return tuple(modules)


def unprivileged_account():
    """Return a non-root account httpd can drop to, when the system has one."""
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


@unittest.skipUnless(all(path.is_file() for path in (*SERVERS, HTPASSWD)),
                      'dist/apache binaries are not built')
class ApacheRuntimeTests(unittest.TestCase):
    def test_binaries_are_statically_linked(self):
        for binary in (*SERVERS, HTPASSWD):
            with self.subTest(binary=binary.name):
                described = subprocess.run(
                    ['file', str(binary)], capture_output=True, text=True, check=True)
                self.assertIn('statically linked', described.stdout)
                linked = subprocess.run(
                    ['ldd', str(binary)], capture_output=True, text=True, check=False)
                self.assertIn('not a dynamic executable', linked.stdout + linked.stderr)

    def test_pinned_apr(self):
        recipe = (PROJECT / 'targets' / 'apache' / 'Dockerfile').read_text()
        apr = re.search(r'^ENV APR_VERSION=(\S+)', recipe, re.M).group(1)
        apu = re.search(r'APU_VERSION=(\S+)', recipe).group(1)
        for binary, mpm in ((HTTPD, 'event'), (HTTPD_PREFORK, 'prefork')):
            with self.subTest(binary=binary.name):
                details = subprocess.run(
                    [binary, '-V'], capture_output=True, text=True, check=True)
                self.assertIn(f'APR {apr}', details.stdout)
                self.assertIn(f'APR-UTIL {apu}', details.stdout)
                self.assertRegex(details.stdout, rf'Server MPM:\s+{mpm}\b')

    def test_reported_version_matches_build(self):
        expected = runtime_util.build_version('apache')
        if expected is None:
            self.skipTest('build did not record a VERSION file')
        for binary in SERVERS:
            with self.subTest(binary=binary.name):
                version = subprocess.run(
                    [binary, '-v'], capture_output=True, text=True, check=True)
                self.assertIn(f'Apache/{expected} ', version.stdout)

    def test_compiled_module_list(self):
        self.assertEqual(compiled_modules(HTTPD), COMPILED_MODULES)
        self.assertEqual(compiled_modules(HTTPD_PREFORK), PREFORK_MODULES)

    def test_htpasswd_creates_apr1_hash(self):
        result = subprocess.run(
            [HTPASSWD, '-nb', 'user', 'secret'],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('user:$apr1$'), result.stdout)

    def test_serves_a_local_page(self):
        account = unprivileged_account()
        if account is None or os.geteuid() != 0:
            self.skipTest('serving a page needs root and a nobody account')
        for binary in SERVERS:
            with self.subTest(binary=binary.name):
                self.serve_page(binary, account)

    def serve_page(self, binary, account):
        user, group = account
        root = Path(tempfile.mkdtemp(prefix=f'httpd-runtime-{binary.name}-'))
        self.addCleanup(shutil.rmtree, root, True)
        htdocs = root / 'htdocs'
        logs = root / 'logs'
        htdocs.mkdir()
        logs.mkdir()
        page = htdocs / 'index.html'
        page.write_text('hello-apache')
        mime = root / 'mime.types'
        mime.write_text('text/html html\n')
        port = free_port()
        config = root / 'httpd.conf'
        config.write_text(
            f'ServerRoot "{root}"\n'
            f'PidFile "{root / "httpd.pid"}"\n'
            f'Listen 127.0.0.1:{port}\n'
            'ServerName localhost\n'
            f'User {user}\n'
            f'Group {group}\n'
            f'DocumentRoot "{htdocs}"\n'
            f'ErrorLog "{logs / "error.log"}"\n'
            'LogLevel error\n'
            f'TypesConfig "{mime}"\n'
            'DirectoryIndex index.html\n'
            f'<Directory "{htdocs}">\n'
            '  Require all granted\n'
            '</Directory>\n'
        )
        for path in (root, htdocs, logs):
            path.chmod(0o755)
        for path in (page, mime, config):
            path.chmod(0o644)

        output = root / 'stdout'
        with output.open('w') as stream:
            # prefork signals its process group on shutdown. A new session
            # keeps that signal off the test runner.
            process = subprocess.Popen(
                [binary, '-f', str(config), '-DFOREGROUND'],
                stdout=stream, stderr=subprocess.STDOUT,
                start_new_session=True)
        self.addCleanup(self.stop_httpd, process)

        url = f'http://127.0.0.1:{port}/'
        body = None
        for _ in range(30):
            if process.poll() is not None:
                break
            try:
                with urllib.request.urlopen(url, timeout=0.2) as response:
                    body = response.read().decode()
                break
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(0.1)
                continue
        self.assertEqual(body, 'hello-apache', output.read_text() + (logs / 'error.log').read_text()
                         if (logs / 'error.log').exists() else output.read_text())

    @staticmethod
    def stop_httpd(process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
