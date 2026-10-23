# curl

[English](../../targets/curl.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh curl
./build-static.sh curl 8.10.1
./build-static.sh curl 8.22.0 --clean
```

| | |
|--|--|
| 預設 | `8.22.0` |
| Alpine | 3.20 |
| 輸出 | `dist/curl/curl` |
| 接受的版本 | `8.x.y` |
| 已實測 | x86_64 上的 `8.22.0`：靜態連結、`--version`，以及啟用憑證驗證的 HTTPS／HTTP/2 下載 |

這個目標靜態連結 OpenSSL、zlib 與 nghttp2，因此有 **HTTPS**、**gzip/deflate** 與 **HTTP/2**。

Tarball 來自 [curl 官方下載封存](https://curl.se/download/)。這個目標未啟用 HTTP/3、SCP/SFTP、LDAP、Brotli、Zstandard、IDN 與 Public Suffix List。

## CA 憑證

執行 curl 的那台機器上，程式會尋找 `/etc/ssl/certs/ca-certificates.crt` 與 `/etc/ssl/certs`。執行檔不含 CA 憑證包。主機若把憑證放在別處，請加上 `--cacert /path/to/ca-bundle.crt`，或設定 `CURL_CA_BUNDLE`。
