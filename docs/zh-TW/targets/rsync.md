# rsync

[English](../../targets/rsync.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh rsync
./build-static.sh rsync 3.4.1
./build-static.sh rsync 3.5.1 --clean
```

| | |
|--|--|
| 預設 | `3.5.1` |
| Alpine | 3.20 |
| 輸出 | `dist/rsync/rsync` |
| 接受的版本 | `3.x.y` |
| 已實測 | x86_64 上的 `3.5.1`：靜態連結、`--version`，以及一次本機檔案複製 |

這個目標靜態連結 OpenSSL、zlib、xxHash、zstd 與 lz4。zlib、zstd 與 lz4 用 Alpine 的靜態套件。Alpine 3.20 沒有靜態 xxHash 套件，所以這個目標從原始碼編譯 xxHash 0.8.3。popt 用 rsync 自帶的那一份。ACL、xattr、iconv 與 IDN 未啟用。`rsync-ssl` 是腳本，所以不匯出。

Tarball 來自 [rsync 下載目錄](https://download.samba.org/pub/rsync/)。

## 複製檔案

```bash
/opt/static/rsync/rsync -a /src/ /dest/
```

以 daemon 執行時，除非加上 `--config`，否則讀取 `/etc/rsyncd.conf`。這個執行檔通常當用戶端用。
