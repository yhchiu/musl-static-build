# openssl

[中文](../zh-TW/targets/openssl.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh openssl
./build-static.sh openssl 3.4.1
./build-static.sh openssl 3.5.9 --clean
```

| | |
|--|--|
| Default | `3.5.9` |
| Alpine | 3.20 |
| Output | `dist/openssl/openssl` |
| Accepted versions | `3.x.y` |
| Checked | `3.5.9` on x86_64: static link, `version`, and one self-signed certificate |

This is the `openssl` command. curl, wget, Apache, and PHP already link their own OpenSSL and do not use this binary. This target builds 3.5 LTS with `no-shared` and `no-module`, then links `apps/openssl` with `-static`. Providers are inside the binary. The binary does not contain a CA bundle.

Tarballs come from the [OpenSSL GitHub releases](https://github.com/openssl/openssl/releases).

## CA certificates

Certificate checks use `/etc/ssl/cert.pem` and `/etc/ssl/certs`, and follow `SSL_CERT_FILE` and `SSL_CERT_DIR`.

```bash
/opt/static/openssl/openssl version
/opt/static/openssl/openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj /CN=localhost
```
