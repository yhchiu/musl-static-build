# curl

[中文](../zh-TW/targets/curl.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh curl
./build-static.sh curl 8.10.1
./build-static.sh curl 8.22.0 --clean
```

| | |
|--|--|
| Default | `8.22.0` |
| Alpine | 3.20 |
| Output | `dist/curl/curl` |
| Accepted versions | `8.x.y` |
| Checked | `8.22.0` on x86_64: static link, `--version`, and an HTTPS download over HTTP/2 with certificate verification |

This target statically links OpenSSL, zlib, and nghttp2, which gives **HTTPS**, **gzip/deflate**, and **HTTP/2**.

Tarballs come from the [official curl download archive](https://curl.se/download/). This target leaves out HTTP/3, SCP/SFTP, LDAP, Brotli, Zstandard, IDN, and the Public Suffix List.

## CA certificates

The binary looks for `/etc/ssl/certs/ca-certificates.crt` and `/etc/ssl/certs` on the machine where curl runs. It does not embed a CA bundle. On a host that stores the bundle elsewhere, pass `--cacert /path/to/ca-bundle.crt` or set `CURL_CA_BUNDLE`.
