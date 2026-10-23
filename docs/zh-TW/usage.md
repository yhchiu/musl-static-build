# 編譯與檢查

[English](../usage.md) · [回到說明](../../README.zh-TW.md)

`build-static.sh` 一次編譯一個程式。它會檢查版本、建立 Alpine 映像、取出靜態執行檔，然後再檢查這些檔案。

## 指令

```text
./build-static.sh <target> [version] [--clean] [--no-test]
./build-static.sh --list
```

沒有參數，或加上 `-h`、`--help`、`help` 時，只顯示說明，不會開始編譯。

| 參數 | 意義 |
|------|------|
| `target` | `php`、`openssh`、`curl`、`wget`、`rsync`、`openssl`、`git`、`apache`、`nginx` 或 `stunnel`。`--list` 會列出腳本找到的目標。 |
| `version` | 可省略。各目標接受的格式見下表。省略時使用該目標的預設版本。 |
| `--clean` | 對 `docker build` 加上 `--no-cache`。可以放在指令的任何位置。 |
| `--no-test` | 編譯成功後略過產物檢查。可以放在指令的任何位置。 |

每次指定一個目標，版本最多一個。沒有目標名稱就只顯示說明，不會編譯。例如 `./build-static.sh 8.5`、`./build-static.sh 10.6p1`、`./build-static.sh --clean`、`./build-static.sh --no-test`。

## 版本格式

| 目標 | 格式 | 例子 |
|------|------|------|
| PHP | `x.y` 表示該系列最新修補版，`x.y.z` 表示指定那一個發行版 | `8.5`、`8.5.11` |
| OpenSSH | `8.xpN`、`9.xpN` 或 `10.xpN` | `8.9p1`、`9.9p2`、`10.6p1` |
| curl | `8.x.y` | `8.22.0` |
| wget | `1.x.y` | `1.25.0` |
| rsync | `3.x.y` | `3.5.1` |
| OpenSSL | `3.x.y` | `3.5.9` |
| Git | `2.x.y` | `2.56.0` |
| Apache httpd | `2.4.x` | `2.4.69` |
| nginx | 完整 `1.x.y`，從 1.26.0 起 | `1.30.6` |
| stunnel | `5.x` | `5.82` |

PHP 的 `x.y` 會在編譯前解析。腳本在 Alpine 容器裡用 `wget` 讀取 [PHP releases API](https://www.php.net/releases/index.php?json&version=8.5)。若要固定某一個 tarball，請寫 `x.y.z`。

## 檔案寫到哪裡

腳本把檔案寫到**目前工作目錄**的 `dist/<target>/`，而不是腳本所在的目錄。你可以從其他目錄執行 `build-static.sh`。編譯成功後會有這些檔案：

| 檔案 | 內容 |
|------|------|
| `dist/<target>/<執行檔>` | 該目標宣告要匯出的每個靜態執行檔 |
| `dist/<target>/VERSION` | 實際編譯的版本 |
| `dist/<target>/Dockerfile` | 該目標的 Dockerfile，加上共用的靜態連結檢查 |

`dist/` 已列入 gitignore。Docker 映像標籤是 `<target>-static-builder`。建置內容（build context）是 `targets/<target>/`。

## 編譯之後的檢查

編譯成功會先寫入 `VERSION`，再執行該目標的產物檢查。檢查會把執行檔回報的版本和這個檔案比對。

檢查需要 `PATH` 上有 `python3` 與 `pytest`。`pytest` 也可以是 `python3` 能匯入的模組。少了其中一個時，編譯仍算成功，版本檔仍會寫入，腳本會印出 `Artifact checks were not run`。`--no-test` 同樣略過檢查，也仍會寫入版本檔。

自行查看執行檔：

```bash
file dist/php/php-cli dist/php/php-cgi dist/php/php-fpm
file dist/openssh/ssh dist/openssh/sshd
ldd dist/openssh/sshd          # 預期：not a dynamic executable
./dist/openssh/ssh -V

file dist/curl/curl
./dist/curl/curl --version

file dist/wget/wget
./dist/wget/wget --version

file dist/rsync/rsync
./dist/rsync/rsync --version

file dist/openssl/openssl
./dist/openssl/openssl version

file dist/git/git
./dist/git/git --version
./dist/git/git --exec-path

file dist/apache/httpd dist/apache/httpd-prefork dist/apache/htpasswd
ldd dist/apache/httpd          # 預期：not a dynamic executable
./dist/apache/httpd -v
./dist/apache/httpd -l

file dist/nginx/nginx dist/stunnel/stunnel
./dist/nginx/nginx -V
./dist/stunnel/stunnel -version
```

HTTPS 下載可以確認 curl 或 wget 在這台機器上讀得到 CA 憑證：

```bash
./dist/curl/curl --fail --location https://curl.se/ -o /dev/null
./dist/wget/wget -O /dev/null https://ftp.gnu.org/gnu/wget/
```

把同一批檔案放到較舊的主機：[在舊主機執行](running-on-old-hosts.md)。
