"""Exercise existing stunnel artifacts, including certificate rejection."""

import http.client
from pathlib import Path
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


STUNNEL = (runtime_util.artifact_dir('stunnel') / 'stunnel').resolve()


@unittest.skipUnless(STUNNEL.is_file(), 'dist/stunnel/stunnel is not built')
class StunnelRuntimeTests(unittest.TestCase):
    def test_static_version_and_openssl(self):
        service.assert_static(self, STUNNEL)
        result = subprocess.run([STUNNEL, '-version'], capture_output=True,
                                text=True, check=True, timeout=10)
        text = result.stdout + result.stderr
        version = runtime_util.build_version('stunnel')
        if version:
            self.assertIn(f'stunnel {version}', text)
        self.assertIn('OpenSSL', text)

    def config(self, root, port, backend, options):
        config = root / f'stunnel-{port}.conf'
        config.write_text(f'''
foreground = yes
syslog = no
pid =
debug = info
[test]
accept = 127.0.0.1:{port}
connect = 127.0.0.1:{backend}
TIMEOUTclose = 0
{options}
''')
        return [STUNNEL, config]

    def test_server_tls12_and_tls13(self):
        with tempfile.TemporaryDirectory(prefix='stunnel-server-') as temp, service.upstream() as backend:
            root = Path(temp)
            cert, key = service.certificate(self, root)
            port = service.free_port()
            command = self.config(root, port, backend,
                                  f'cert = {cert}\nkey = {key}\nsslVersionMin = TLSv1.2')
            with service.running(self, command, port, root):
                for version in (ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3):
                    with self.subTest(version=version):
                        context = ssl.create_default_context(cafile=str(cert))
                        context.minimum_version = context.maximum_version = version
                        conn = http.client.HTTPSConnection('localhost', port, context=context, timeout=5)
                        try:
                            conn.request('GET', '/')
                            response = conn.getresponse()
                            self.assertEqual(response.status, 200)
                            self.assertEqual(response.read(), b'hello-upstream')
                        finally:
                            conn.close()

    def test_client_verification_and_rejection(self):
        with tempfile.TemporaryDirectory(prefix='stunnel-client-') as temp:
            root = Path(temp)
            cert, key = service.certificate(self, root)
            other = root / 'other-ca'
            other.mkdir()
            untrusted_ca, _ = service.certificate(self, other)
            with service.upstream(cert, key) as backend:
                for hostname, ca, accepted in (
                    ('localhost', cert, True),
                    ('wrong.example', cert, False),
                    ('localhost', untrusted_ca, False),
                ):
                    with self.subTest(hostname=hostname, ca=ca):
                        port = service.free_port()
                        command = self.config(root, port, backend, f'''
client = yes
verifyChain = yes
CAfile = {ca}
checkHost = {hostname}
sni = localhost
sslVersionMin = TLSv1.2
''')
                        with service.running(self, command, port, root):
                            conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                            try:
                                if accepted:
                                    conn.request('GET', '/')
                                    self.assertEqual(conn.getresponse().read(), b'hello-upstream')
                                else:
                                    # A reset/EOF is rejection; a timeout is a failure.
                                    with self.assertRaises((ConnectionResetError, BrokenPipeError,
                                                            http.client.RemoteDisconnected)):
                                        conn.request('GET', '/')
                                        conn.getresponse()
                            finally:
                                conn.close()


if __name__ == '__main__':
    unittest.main()
