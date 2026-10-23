# musl-static-build

本專案針對無法升級 glibc 的舊 Linux 主機，編譯可直接複製過去執行、**完全靜態連結的 musl 執行檔**。優先收錄的工具，是那些**繼續使用舊版會有重大安全風險，或缺少必要功能與協定相容性，但新版又因 glibc 或相依函式庫限制而難以部署**的程式。

典型需求包括修補遠端連線工具的已知安全漏洞，以及讓下載工具支援連接現行服務所需的 TLS 版本與演算法。

目前可編譯的程式包括 **PHP、OpenSSH、curl、wget、rsync、OpenSSL、Git、Apache httpd、nginx、stunnel**。

在新版系統上編譯的程式，放到舊主機時常會停在 `GLIBC_2.xx not found`。這個專案在 Docker 裡用 Alpine Linux 與 musl，把程式和它需要的函式庫連成單一檔案。舊主機維持原來的系統函式庫，並可同時執行這個新檔案。

請在有 Docker 的機器上編譯，再把成品複製到舊主機。執行檔的 CPU 架構與執行 Docker 的機器相同。目前實測過的版本是 x86_64。

English: [README.md](README.md)

## 可編譯的程式

| 程式 | 預設版本 | 輸出 |
|------|----------|------|
| PHP 8.x | `8.5`（該系列最新修補版） | `dist/php/php-cli`、`dist/php/php-cgi`、`dist/php/php-fpm` |
| OpenSSH 8.x / 9.x / 10.x | `9.9p2` | `dist/openssh/`（`ssh`、`sshd`、`sftp-server` 等） |
| curl 8.x | `8.22.0` | `dist/curl/curl` |
| wget 1.x | `1.25.0` | `dist/wget/wget` |
| rsync 3.x | `3.5.1` | `dist/rsync/rsync` |
| OpenSSL 3.x | `3.5.9` | `dist/openssl/openssl` |
| Git 2.x | `2.56.0` | `dist/git/`（`git`、`git-remote-https` 等） |
| Apache httpd 2.4.x | `2.4.69` | `dist/apache/httpd`、`dist/apache/httpd-prefork`、`dist/apache/htpasswd` |
| nginx 1.x | `1.30.6` | `dist/nginx/nginx` |
| stunnel 5.x | `5.82` | `dist/stunnel/stunnel` |

若 `file` 未回報 `statically linked`，編譯會停止。

## 編譯機需要什麼

- Docker
- 可連外的網路，用來拉取 Alpine 映像與下載原始碼
- Bash

舊主機不需要 Docker，也不需要較新的 glibc。若核心太舊、缺少程式用到的系統呼叫，執行時仍可能失敗。

## 編譯

```bash
chmod +x build-static.sh

./build-static.sh php
./build-static.sh openssh
./build-static.sh curl
./build-static.sh wget
./build-static.sh rsync
./build-static.sh openssl
./build-static.sh git
./build-static.sh apache
./build-static.sh nginx
./build-static.sh stunnel
```

成品寫在你執行腳本時的工作目錄，路徑是 `dist/<程式>/`。`./build-static.sh` 會顯示說明。`./build-static.sh --list` 會列出每個目標，以及它接受的版本格式。

指定版本，或略過 Docker 快取重編：

```bash
./build-static.sh php 8.4
./build-static.sh php 8.5.11
./build-static.sh openssh 8.9p1
./build-static.sh curl 8.22.0 --clean
```

參數、版本格式，以及編譯後的檢查：[docs/zh-TW/usage.md](docs/zh-TW/usage.md)。

## 複製到舊主機

```bash
scp -r dist/curl oldhost:/opt/static/
ssh oldhost /opt/static/curl/curl --version
```

有些路徑在編譯時就寫進執行檔，所以把 `dist/` 解到舊主機之後，還需要對應的設定：

- **curl** 與 **wget** 會讀取主機上的 CA 憑證。執行檔裡沒有憑證包。
- **sshd** 讀取 `/etc/ssh/sshd_config`，並從 `/usr/libexec` 啟動 `sftp-server`、`sshd-session`、`sshd-auth`。
- **php-fpm** 預設讀取 `/usr/local/etc/php-fpm.conf`，也可以用 `-y` 指定其他檔案。pool 裡的 `user` 與 `group` 必須是這台機器上存在的帳號。
- **httpd** 預設讀取 `/etc/httpd/httpd.conf`，也可以用 `-f` 指定其他檔案。模組已編譯進執行檔，設定檔不要寫 `LoadModule`。
- **nginx** 預設讀取 `/etc/nginx/nginx.conf`，也可以用 `-c` 指定其他檔案。模組已內建，不要寫 `load_module`；日誌與暫存目錄的準備方式見程式文件。
- **stunnel** 讀取 `/etc/stunnel/stunnel.conf` 或命令列指定的檔名。設定檔、CA 憑證包及所需的憑證／私鑰需另外提供。

各程式要怎麼擺放：[docs/zh-TW/running-on-old-hosts.md](docs/zh-TW/running-on-old-hosts.md)。

| 程式 | 這個目標包含什麼 |
|------|------------------|
| [PHP](docs/zh-TW/targets/php.md) | CLI、CGI 與 PHP-FPM，常用擴充功能已編譯進去 |
| [OpenSSH](docs/zh-TW/targets/openssh.md) | 用戶端工具與 `sshd` |
| [curl](docs/zh-TW/targets/curl.md) | HTTPS、gzip/deflate、HTTP/2 |
| [wget](docs/zh-TW/targets/wget.md) | HTTPS、gzip、正規表示式 |
| [rsync](docs/zh-TW/targets/rsync.md) | 複製檔案，含 zstd、lz4 與 xxHash |
| [OpenSSL](docs/zh-TW/targets/openssl.md) | `openssl` 指令，含 TLS 1.3 |
| [Git](docs/zh-TW/targets/git.md) | `git` 與 HTTPS 輔助程式放在同一目錄 |
| [Apache httpd](docs/zh-TW/targets/apache.md) | `httpd`（event）、`httpd-prefork` 與 `htpasswd`，模組已編譯進去 |
| [nginx](docs/zh-TW/targets/nginx.md) | 內建 HTTPS、HTTP/2/3、proxy／cache、FastCGI、gzip／Brotli、XSLT、WebDAV 與 stream 模組 |
| [stunnel](docs/zh-TW/targets/stunnel.md) | 支援憑證驗證的 TLS client／server proxy |

## 已實測的版本

| 程式 | 已實測版本 |
|------|------------|
| PHP | x86_64 上的 `8.5.11`；`8.4`（未記錄確切修補版號） |
| OpenSSH | x86_64 上的 `9.9p2`、`10.6p1` |
| curl | x86_64 上的 `8.22.0` |
| wget | x86_64 上的 `1.25.0` |
| rsync | x86_64 上的 `3.5.1` |
| OpenSSL | x86_64 上的 `3.5.9` |
| Git | x86_64 上的 `2.56.0` |
| Apache httpd | x86_64 上的 `2.4.69` |
| nginx | x86_64 上的 `1.30.6` |
| stunnel | x86_64 上的 `5.82` |

版本參數還接受同一系列的其他發行版。上表只列出實際編譯並執行過的版本。細節見各程式頁面。

## 參與開發

新增 target 應同時符合以下條件：

1. **有明確的升級必要性**：舊版存在與實際使用情境相關的重大安全問題，或無法滿足必要功能、協定相容性需求。
2. **新版在舊主機上有部署障礙**：受到 glibc 或相依函式庫版本限制，且缺少可直接使用的合適成品。
3. **本專案的建置方式能解決障礙**：可產出完全靜態連結的 musl 執行檔，並驗證所需功能。

工具常用、版本較舊，或容易靜態編譯，本身不足以構成新增 target 的理由。

- [新增一個程式](docs/zh-TW/adding-a-target.md)
- [執行測試](docs/zh-TW/development.md)
- [文件索引](docs/zh-TW/README.md)
