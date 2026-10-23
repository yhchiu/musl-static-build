"""Local service fixtures for the nginx and stunnel artifact checks."""

from contextlib import contextmanager
import http.server
import shutil
import socket
import ssl
import subprocess
import threading
import time


def assert_static(test, binary):
    result = subprocess.run(['file', str(binary)], capture_output=True,
                            text=True, check=True, timeout=10)
    test.assertIn('statically linked', result.stdout)
    result = subprocess.run(['ldd', str(binary)], capture_output=True,
                            text=True, check=False, timeout=10)
    test.assertIn('not a dynamic executable', result.stdout + result.stderr)


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def certificate(test, root):
    openssl = shutil.which('openssl')
    if not openssl:
        test.skipTest('TLS checks need the openssl command to create a test certificate')
    cert, key = root / 'cert.pem', root / 'key.pem'
    subprocess.run([openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                    '-days', '1', '-subj', '/CN=localhost',
                    '-addext', 'subjectAltName=DNS:localhost',
                    '-keyout', str(key), '-out', str(cert)],
                   capture_output=True, check=True, timeout=20)
    return cert, key


@contextmanager
def running(test, command, port, root):
    log = root / f'service-{port}.log'
    with log.open('w') as output:
        proc = subprocess.Popen([str(arg) for arg in command], stdout=output,
                                stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 10
            while True:
                if proc.poll() is not None:
                    test.fail(f'Service exited ({proc.returncode}): {log.read_text()}')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.2):
                        break
                except OSError:
                    if time.monotonic() >= deadline:
                        test.fail(f'Service did not listen: {log.read_text()}')
                    time.sleep(.05)
            yield proc
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


class Handler(http.server.BaseHTTPRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            # TLS rejection tests deliberately abort before sending HTTP.
            pass

    def do_GET(self):
        body = b'hello-upstream'
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@contextmanager
def upstream(cert=None, key=None):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    if cert:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
