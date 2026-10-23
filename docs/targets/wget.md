# wget

[中文](../zh-TW/targets/wget.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh wget
./build-static.sh wget 1.21.4
./build-static.sh wget 1.25.0 --clean
```

| | |
|--|--|
| Default | `1.25.0` |
| Alpine | 3.20 |
| Output | `dist/wget/wget` |
| Accepted versions | `1.x.y` |
| Checked | `1.25.0` on x86_64: static link, `--version`, and an HTTPS download with certificate verification |

This target statically links OpenSSL, zlib, and PCRE2, which gives **HTTPS**, **gzip**, and regular expressions.

Tarballs come from the [official GNU FTP archive](https://ftp.gnu.org/gnu/wget/). This target leaves out Metalink, IRI/IDN, the Public Suffix List, libuuid, and native-language translations.

## CA certificates

HTTPS uses OpenSSL's default locations, `/etc/ssl/cert.pem` and `/etc/ssl/certs`, and honors `SSL_CERT_FILE` and `SSL_CERT_DIR`. The binary does not embed a CA bundle. On a host that stores the bundle elsewhere, pass `--ca-certificate /path/to/ca-bundle.crt`.
