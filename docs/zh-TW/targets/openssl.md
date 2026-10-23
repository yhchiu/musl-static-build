# openssl

[English](../../targets/openssl.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh openssl
./build-static.sh openssl 3.4.1
./build-static.sh openssl 3.5.9 --clean
```

| | |
|--|--|
| 預設 | `3.5.9` |
| Alpine | 3.20 |
| 輸出 | `dist/openssl/openssl` |
| 接受的版本 | `3.x.y` |
| 已實測 | x86_64 上的 `3.5.9`：靜態連結、`version`，以及一張自簽憑證 |

這是 `openssl` 指令。curl、wget、Apache 與 PHP 各自連結自己的 OpenSSL，不使用這個執行檔。這個目標以 3.5 LTS 搭配 `no-shared` 與 `no-module` 編譯，再以 `-static` 連結 `apps/openssl`。Provider 在執行檔裡面。執行檔不含 CA 憑證包。

Tarball 來自 [OpenSSL GitHub releases](https://github.com/openssl/openssl/releases)。

## CA 憑證

憑證檢查使用 `/etc/ssl/cert.pem` 與 `/etc/ssl/certs`，並遵循 `SSL_CERT_FILE` 與 `SSL_CERT_DIR`。

```bash
/opt/static/openssl/openssl version
/opt/static/openssl/openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj /CN=localhost
```
