# wget

[English](../../targets/wget.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh wget
./build-static.sh wget 1.21.4
./build-static.sh wget 1.25.0 --clean
```

| | |
|--|--|
| 預設 | `1.25.0` |
| Alpine | 3.20 |
| 輸出 | `dist/wget/wget` |
| 接受的版本 | `1.x.y` |
| 已實測 | x86_64 上的 `1.25.0`：靜態連結、`--version`，以及啟用憑證驗證的 HTTPS 下載 |

這個目標靜態連結 OpenSSL、zlib 與 PCRE2，因此有 **HTTPS**、**gzip** 與正規表示式。

Tarball 來自 [GNU 官方 FTP 封存](https://ftp.gnu.org/gnu/wget/)。這個目標未啟用 Metalink、IRI/IDN、Public Suffix List、libuuid 與多語系翻譯。

## CA 憑證

HTTPS 使用 OpenSSL 的預設位置 `/etc/ssl/cert.pem` 與 `/etc/ssl/certs`，並遵循 `SSL_CERT_FILE` 與 `SSL_CERT_DIR`。執行檔不含 CA 憑證包。主機若把憑證放在別處，請加上 `--ca-certificate /path/to/ca-bundle.crt`。
