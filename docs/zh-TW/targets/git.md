# git

[English](../../targets/git.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh git
./build-static.sh git 2.47.2
./build-static.sh git 2.56.0 --clean
```

| | |
|--|--|
| 預設 | `2.56.0` |
| Alpine | 3.20 |
| 輸出 | `dist/git/`（`git` 與下面列出的輔助程式） |
| 接受的版本 | `2.x.y` |
| 已實測 | x86_64 上的 `2.56.0`：靜態連結、`--version`、`--exec-path`，以及一次本機 commit |

這個目標在同一映像先編一份小的靜態 libcurl（OpenSSL 與 zlib，不含 HTTP/2、Brotli、IDN），再讓 Git 連結這份 libcurl 與 Alpine 的靜態 OpenSSL。它不使用 [openssl](openssl.md) 或 [curl](curl.md) 目標。PCRE2 有啟用。musl 沒有 `REG_STARTEND`，所以這個目標改用 Git 自帶的 regex。Gettext、Perl、Python、Tcl/Tk 與 Rust 未啟用。

`RUNTIME_PREFIX` 有打開。`bindir` 與 `gitexecdir` 都是相對路徑 `git`，所以輔助程式跟 `git` 放在名為 `git` 的同一目錄時就能被找到。

匯出的檔案：

- `git`
- `git-receive-pack`、`git-upload-pack`、`git-upload-archive`
- `git-shell`
- `git-http-backend`
- `git-remote-http`、`git-remote-https`

shell 腳本不匯出。範本目錄不內嵌。`git init` 仍可建立倉庫，只是沒有範例 hook。

Tarball 來自 [kernel.org](https://www.kernel.org/pub/software/scm/git/)。

## HTTPS

`git-remote-https` 使用 OpenSSL 的憑證路徑 `/etc/ssl/cert.pem` 與 `/etc/ssl/certs`，並遵循 `SSL_CERT_FILE` 與 `SSL_CERT_DIR`。執行檔不含 CA 憑證包。
