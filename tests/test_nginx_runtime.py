"""Exercise existing nginx artifacts on loopback; no Docker or Internet."""

import grp
import gzip
import http.client
import os
from pathlib import Path
import pwd
import socket
import ssl
import subprocess
import tempfile
import unittest

try:
    import runtime_util
    import service_util as service
except ImportError:
    from tests import runtime_util
    from tests import service_util as service


NGINX = (runtime_util.artifact_dir('nginx') / 'nginx').resolve()
MODULES = (
    'http_ssl', 'http_v2', 'http_v3', 'http_realip', 'http_addition',
    'http_xslt', 'http_sub', 'http_dav', 'http_flv', 'http_mp4',
    'http_gunzip', 'http_gzip_static', 'http_auth_request',
    'http_random_index', 'http_secure_link', 'http_slice', 'http_stub_status',
    'stream_ssl', 'stream_realip', 'stream_ssl_preread',
)


@unittest.skipUnless(NGINX.is_file(), 'dist/nginx/nginx is not built')
class NginxRuntimeTests(unittest.TestCase):
    def test_static_version_and_modules(self):
        service.assert_static(self, NGINX)
        result = subprocess.run([NGINX, '-V'], capture_output=True, text=True,
                                check=True, timeout=10)
        version = runtime_util.build_version('nginx')
        if version:
            self.assertIn(f'nginx/{version}', result.stderr)
        for module in MODULES:
            self.assertIn(f'--with-{module}_module', result.stderr)
        self.assertIn('--add-module=/usr/src/ngx_brotli', result.stderr)
        self.assertNotIn('=dynamic', result.stderr)

    def config(self, root, http):
        # Keep the test process under the caller's uid, including when the
        # suite runs as root. Only ephemeral loopback ports are exposed.
        user = pwd.getpwuid(os.geteuid()).pw_name
        group = grp.getgrgid(os.getegid()).gr_name
        paths = '\n'.join(
            f'{kind}_temp_path "{root / kind}";'
            for kind in ('client_body', 'proxy', 'fastcgi', 'uwsgi', 'scgi'))
        config = root / 'nginx.conf'
        config.write_text(f'''
daemon off;
master_process off;
user {user} {group};
pid "{root / 'nginx.pid'}";
error_log stderr notice;
events {{ worker_connections 64; }}
http {{
    {paths}
    access_log off;
    default_type text/plain;
    {http}
}}
''')
        command = [NGINX, '-p', str(root) + '/', '-c', config, '-e', 'stderr']
        checked = subprocess.run([*command, '-t'], capture_output=True,
                                 text=True, timeout=10)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        return command

    def test_http_proxy_rewrite_auth_and_compression(self):
        with tempfile.TemporaryDirectory(prefix='nginx-http-') as temp, service.upstream() as backend:
            root = Path(temp)
            body = b'hello-nginx\n' * 256
            (root / 'index.txt').write_bytes(body)
            (root / 'index.txt.gz').write_bytes(gzip.compress(body))
            port = service.free_port()
            command = self.config(root, f'''
server {{
    listen 127.0.0.1:{port};
    root "{root}";
    gzip on; gzip_min_length 1; gzip_types text/plain;
    brotli on; brotli_min_length 1; brotli_types text/plain;
    location / {{ try_files $uri =404; }}
    location = /old {{ rewrite ^ /index.txt last; }}
    location /proxy {{ proxy_pass http://127.0.0.1:{backend}; }}
    location = /auth {{ internal; return 204; }}
    location = /deny {{ internal; return 403; }}
    location = /allowed {{ auth_request /auth; proxy_pass http://127.0.0.1:{backend}; }}
    location = /denied {{ auth_request /deny; proxy_pass http://127.0.0.1:{backend}; }}
    location = /status {{ stub_status; }}
    location /precompressed/ {{ alias "{root}/"; gzip_static on; gzip off; }}
}}
''')
            with service.running(self, command, port, root):
                def request(path, headers=None):
                    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                    try:
                        conn.request('GET', path, headers=headers or {})
                        response = conn.getresponse()
                        return response.status, dict(response.getheaders()), response.read()
                    finally:
                        conn.close()
                for path in ('/index.txt', '/old'):
                    status, _, data = request(path)
                    self.assertEqual(status, 200)
                    self.assertEqual(data, body)
                for path in ('/proxy', '/allowed'):
                    self.assertEqual(request(path)[2], b'hello-upstream')
                self.assertEqual(request('/denied')[0], 403)
                self.assertIn(b'Active connections:', request('/status')[2])
                for path in ('/index.txt', '/precompressed/index.txt'):
                    status, headers, data = request(path, {'Accept-Encoding': 'gzip'})
                    self.assertEqual(status, 200)
                    self.assertEqual(headers.get('Content-Encoding'), 'gzip')
                    self.assertEqual(gzip.decompress(data), body)
                status, headers, data = request('/index.txt', {'Accept-Encoding': 'br'})
                self.assertEqual(status, 200)
                self.assertEqual(headers.get('Content-Encoding'), 'br')
                self.assertGreater(len(data), 0)
                self.assertLess(len(data), len(body))

    def test_php_fpm_integration(self):
        fpm = (runtime_util.artifact_dir('php') / 'php-fpm').resolve()
        if not fpm.is_file():
            self.skipTest('PHP-FPM integration needs dist/php/php-fpm')
        try:
            account = pwd.getpwnam('nobody') if os.geteuid() == 0 else pwd.getpwuid(os.geteuid())
            group = grp.getgrgid(account.pw_gid).gr_name
        except KeyError:
            self.skipTest('PHP-FPM integration needs a worker account')
        with tempfile.TemporaryDirectory(prefix='nginx-fpm-') as temp:
            root = Path(temp)
            root.chmod(0o755)
            script = root / 'index.php'
            script.write_text('<?php echo "hello-" . $_GET["name"];')
            script.chmod(0o644)
            backend = service.free_port()
            pool = root / 'php-fpm.conf'
            pool.write_text(f'''
[global]
daemonize = no
error_log = {root / 'fpm.log'}
[www]
listen = 127.0.0.1:{backend}
user = {account.pw_name}
group = {group}
pm = static
pm.max_children = 1
''')
            with service.running(self, [fpm, '-F', '-y', pool], backend, root):
                port = service.free_port()
                command = self.config(root, f'''
server {{
    listen 127.0.0.1:{port};
    root "{root}";
    location ~ [.]php$ {{
        try_files $uri =404;
        fastcgi_pass 127.0.0.1:{backend};
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param REQUEST_METHOD $request_method;
        fastcgi_param QUERY_STRING $query_string;
        fastcgi_param REDIRECT_STATUS 200;
    }}
}}
''')
                with service.running(self, command, port, root):
                    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                    try:
                        conn.request('GET', '/index.php?name=fastcgi')
                        response = conn.getresponse()
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.read(), b'hello-fastcgi')
                        conn.request('GET', '/missing.php')
                        self.assertEqual(conn.getresponse().status, 404)
                    finally:
                        conn.close()

    def test_https_and_http2(self):
        with tempfile.TemporaryDirectory(prefix='nginx-tls-') as temp:
            root = Path(temp)
            cert, key = service.certificate(self, root)
            port = service.free_port()
            command = self.config(root, f'''
server {{
    listen 127.0.0.1:{port} ssl;
    http2 on;
    ssl_certificate "{cert}";
    ssl_certificate_key "{key}";
    ssl_protocols TLSv1.2 TLSv1.3;
    location / {{ return 200 "hello-tls"; }}
}}
''')
            with service.running(self, command, port, root):
                for version in (ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3):
                    with self.subTest(version=version):
                        context = ssl.create_default_context(cafile=str(cert))
                        context.minimum_version = context.maximum_version = version
                        conn = http.client.HTTPSConnection('localhost', port, context=context, timeout=5)
                        try:
                            conn.request('GET', '/')
                            self.assertEqual(conn.getresponse().read(), b'hello-tls')
                        finally:
                            conn.close()
                context = ssl.create_default_context(cafile=str(cert))
                context.set_alpn_protocols(['h2'])
                with socket.create_connection(('127.0.0.1', port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname='localhost') as tls:
                        self.assertEqual(tls.selected_alpn_protocol(), 'h2')
                        tls.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n' + b'\0\0\0\x04\0\0\0\0\0')
                        frame = b''
                        while len(frame) < 9:
                            chunk = tls.recv(9 - len(frame))
                            self.assertTrue(chunk, 'HTTP/2 connection closed without SETTINGS')
                            frame += chunk
                        self.assertEqual(frame[3], 4)  # SETTINGS frame


if __name__ == '__main__':
    unittest.main()
