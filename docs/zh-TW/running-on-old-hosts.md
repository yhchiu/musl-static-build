# 在舊主機執行

[English](../running-on-old-hosts.md) · [回到說明](../../README.zh-TW.md)

編譯機和舊主機做的事不同。Docker 跑在編譯機上。舊主機只接收編譯好的檔案。

## 1. CPU 架構要相同

執行檔的架構跟跑 Docker 的機器一樣。x86_64 編譯出來的檔案要放到 x86_64 主機。請複製到相同架構的機器。

## 2. 複製整個目錄

以下用 `dist/curl/` 當例子，在編譯機上執行：

```bash
scp -r dist/curl oldhost:/opt/static/
ssh oldhost /opt/static/curl/curl --version
```

在舊主機上，`file` 仍應回報 `statically linked`。`ldd` 應回報 `not a dynamic executable`。非常舊的 `file` 有時只會寫 `ELF` 和 `executable`；那種情況下以 `ldd` 為準。

可以用完整路徑執行，也可以把該目錄加進 `PATH`。不一定要取代發行版的 `/usr/bin/curl`。把靜態檔留在 `/opt/static/`，原來的套件可以繼續留在系統裡。

## 3. 補上執行檔仍會讀取的檔案

靜態連結處理的是函式庫。設定檔、CA 憑證，以及少數輔助程式仍放在主機上。

### curl

```bash
/opt/static/curl/curl --version
/opt/static/curl/curl --fail --location https://example.com/ -o /dev/null
```

HTTPS 會讀 `/etc/ssl/certs/ca-certificates.crt` 或 `/etc/ssl/certs`。主機若把憑證放在別處：

```bash
/opt/static/curl/curl --cacert /path/to/ca-bundle.crt https://example.com/
```

`CURL_CA_BUNDLE` 也可以指定同一個檔案。這個目標有哪些功能、略過哪些協定，見 [curl](targets/curl.md)。

### wget

```bash
/opt/static/wget/wget --version
/opt/static/wget/wget -O /dev/null https://example.com/
```

HTTPS 使用 OpenSSL 的預設位置 `/etc/ssl/cert.pem` 與 `/etc/ssl/certs`，並遵循 `SSL_CERT_FILE` 與 `SSL_CERT_DIR`。單次指定其他憑證：

```bash
/opt/static/wget/wget --ca-certificate /path/to/ca-bundle.crt https://example.com/
```

細節見 [wget](targets/wget.md)。

### PHP

`php-cli` 是命令列程式。`php-cgi` 是 CGI 程式。`php-fpm` 是 FastCGI 程序管理器。

```bash
/opt/static/php/php-cli -v
/opt/static/php/php-cli -m
```

這個目標不含 `php.ini`。需要設定時再指定：

```bash
/opt/static/php/php-cli -c /etc/php.ini -v
```

`php-fpm` 的設定放在主機上。未指定 `-y` 時，它讀取 `/usr/local/etc/php-fpm.conf`。pool 裡的 `user` 與 `group` 必須是這台機器上存在的帳號。以 root 啟動，worker 才能切換到那個帳號。請用執行檔的絕對路徑啟動。

```ini
[global]
error_log = /var/log/php-fpm.log
pid = /var/run/php-fpm.pid

[www]
user = nobody
group = nobody
listen = /var/run/php-fpm.sock
listen.owner = nobody
listen.group = nobody
listen.mode = 0660
pm = static
pm.max_children = 5
```

`group = nobody` 適用於部分發行版。其他發行版用的是 `nogroup`。請改成該主機上存在的群組。網頁伺服器的帳號必須連得上這個 socket。啟動前先建立日誌目錄、PID 檔所在的目錄，以及 socket 所在的目錄：

```bash
/opt/static/php/php-fpm -y /etc/php-fpm.conf -t
/opt/static/php/php-fpm -y /etc/php-fpm.conf -F
```

`-F` 會讓行程留在前景。拿掉 `-F` 則在背景執行，PID 寫入 `pid` 指定的檔案。worker 需要 ini 設定時，加上 `-c /etc/php.ini`。pool 接受的腳本檔名以 `.php` 結尾。

這個專案的 `httpd` 含有 `mod_proxy_fcgi`。下面這段用的是同一個 socket：

```apache
<FilesMatch "\.php$">
    SetHandler "proxy:unix:/var/run/php-fpm.sock|fcgi://localhost"
</FilesMatch>
```

擴充功能，以及內建 curl 擴充的限制，見 [PHP](targets/php.md)。

### OpenSSH

用戶端程式（`ssh`、`scp`、`sftp`、`ssh-keygen`、`ssh-keyscan`、`ssh-add`、`ssh-agent`）放在任何目錄都能執行：

```bash
/opt/static/openssh/ssh -V
/opt/static/openssh/ssh user@other-host
```

`sshd` 不同。它固定尋找編譯時寫入的路徑：

| `dist/openssh/` 裡的檔案 | `sshd` 尋找的位置 |
|--------------------------|-------------------|
| `sftp-server` | `/usr/libexec/sftp-server` |
| `sshd-session`（OpenSSH 9.8 起） | `/usr/libexec/sshd-session` |
| `sshd-auth`（OpenSSH 10.0 起） | `/usr/libexec/sshd-auth` |
| 設定檔 | `/etc/ssh/sshd_config` |

啟動 `sshd` 之前，請把這些輔助程式複製到 `/usr/libexec/`。把它們留在 `/opt/static/openssh/`、跟 `sshd` 放在一起，並不會改變尋找路徑。權限分離使用使用者 `sshd` 與目錄 `/var/empty`。

這個目標未包含 PAM、Kerberos、SELinux、host-based 認證、PKCS#11 與 security key 輔助程式。主機金鑰與 `authorized_keys` 仍可使用。機器上若還沒有主機金鑰，用這份靜態的 `ssh-keygen` 建立。

依版本出現的檔案，以及 Alpine／OpenSSL 的選擇，見 [OpenSSH](targets/openssh.md)。

### Apache httpd

三個執行檔是 `httpd`、`httpd-prefork` 與 `htpasswd`。`httpd` 是 event MPM。`httpd-prefork` 是 prefork MPM。模組已編譯進兩台伺服器，所以給這兩個執行檔的設定不要寫 `LoadModule`。同一份設定檔可以給兩者使用。HTTP/2 要用 `httpd`。兩台伺服器若共用同一個 `Listen` 埠，一次只啟動一台。

預設設定檔是 `/etc/httpd/httpd.conf`，預設 MIME 檔是 `/etc/httpd/mime.types`。`httpd -f` 可以改用別的設定檔。`User` 與 `Group` 必須是這台機器上存在的非 root 帳號。以這種方式啟動需要 root，httpd 才能切換到那個帳號。

下面這份短設定只服務一個目錄，結構與專案裡的 HTTP 檢查相同：

```apache
ServerRoot "/var/www"
PidFile "/var/run/httpd.pid"
Listen 8080
ServerName localhost

User nobody
Group nobody

DocumentRoot "/var/www/htdocs"
ErrorLog "/var/log/httpd-error.log"
LogLevel error
TypesConfig "/etc/httpd/mime.types"
DirectoryIndex index.html

<Directory "/var/www/htdocs">
    Require all granted
</Directory>
```

`/etc/httpd/mime.types` 可以很短，例如一行 `text/html html`。啟動前先建立文件根目錄、日誌目錄，以及 PID 檔所在的目錄：

```bash
/opt/static/apache/httpd -f /etc/httpd/httpd.conf -t
/opt/static/apache/httpd -f /etc/httpd/httpd.conf -DFOREGROUND
/opt/static/apache/httpd-prefork -f /etc/httpd/httpd.conf -DFOREGROUND
```

`Group nobody` 適用於部分發行版。其他發行版用的是 `nogroup`。請改成該主機上存在的群組。

`htpasswd` 只需要一個檔名：

```bash
/opt/static/apache/htpasswd -nb user secret
```

模組清單，以及 `mod_dbd` 連得到什麼，見 [Apache httpd](targets/apache.md)。

## rsync

把 `dist/rsync/rsync` 複製到舊主機。本機複製不需要額外檔案：

```bash
/opt/static/rsync/rsync -a /src/ /dest/
```

`rsync --daemon` 會讀 `/etc/rsyncd.conf`，除非加上 `--config`。這個建置不含 ACL、xattr、iconv 與 IDN。

## openssl

把 `dist/openssl/openssl` 複製到舊主機。執行檔不含 CA 憑證包。憑證檢查使用 `/etc/ssl/cert.pem` 與 `/etc/ssl/certs`，並遵循 `SSL_CERT_FILE` 與 `SSL_CERT_DIR`。

```bash
/opt/static/openssl/openssl version
/opt/static/openssl/openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj /CN=localhost
```

細節見 [openssl](targets/openssl.md)。

## git

把整個 `dist/git/` 目錄複製過去，並保持目錄名稱是 `git`。輔助程式必須跟 `git` 放在一起。用絕對路徑執行時，`git --exec-path` 會回報這個目錄。

```bash
/opt/static/git/git --version
/opt/static/git/git --exec-path
```

這個建置不含範本目錄，所以 `git init` 建立的倉庫沒有範例 hook。第一次 commit 前先設定名字與信箱：

```bash
/opt/static/git/git config --global user.name "Your Name"
/opt/static/git/git config --global user.email "you@example.com"
```

HTTPS 使用 `/etc/ssl/cert.pem` 與 `/etc/ssl/certs`，並遵循 `SSL_CERT_FILE` 與 `SSL_CERT_DIR`。執行檔不含 CA 憑證包。

細節見 [git](targets/git.md)。

## nginx

把 `dist/nginx/nginx` 複製到舊主機。模組已編入，不要使用 `load_module`。預設設定檔是 `/etc/nginx/nginx.conf`，設定檔、日誌／暫存目錄與憑證仍需放在主機上。啟動前先檢查：

```bash
/opt/static/nginx/nginx -V
/opt/static/nginx/nginx -c /etc/nginx/nginx.conf -t
/opt/static/nginx/nginx -c /etc/nginx/nginx.conf -g 'daemon off;'
```

編入的 worker 帳號／群組是 `nobody/nobody`；請用 `user` 改成主機已有的帳號／群組，例如 `nobody nogroup`。[nginx 文件](targets/nginx.md) 提供目錄準備、獨立設定範例、PHP-FPM 整合與模組清單。

## stunnel

把 `dist/stunnel/stunnel` 複製到舊主機，並提供設定檔。Client 應使用 `verifyChain`、`CAfile` 與 `checkHost` 同時驗證憑證鏈及對端主機名稱；server 則需要自己的憑證與私鑰。

```bash
/opt/static/stunnel/stunnel -version
/opt/static/stunnel/stunnel /etc/stunnel/stunnel.conf
```

[stunnel 文件](targets/stunnel.md) 提供 client／server 範例，並說明外部檔案與停用的功能。
