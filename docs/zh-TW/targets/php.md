# PHP

[English](../../targets/php.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh php              # 最新的 8.5.x
./build-static.sh php 8.4          # 最新的 8.4.x
./build-static.sh php 8.5.11       # 指定那一個發行版
```

| | |
|--|--|
| 預設 | `8.5`，編譯前會解析成最新的 `8.5.x` tarball |
| Alpine | 3.20 |
| 輸出 | `dist/php/php-cli`、`dist/php/php-cgi`、`dist/php/php-fpm` |
| 已實測 | x86_64 上的 `8.5.11`。三個執行檔都是靜態連結，回報 8.5.11，`php-fpm` 並成功回應一次 FastCGI 請求。`8.4` 較早編譯並執行過，確切修補版號沒有記錄。 |

`x.y` 會透過 Alpine 容器查詢 [PHP releases API](https://www.php.net/releases/index.php?json&version=8.5)。`x.y.z` 則下載你指定的那個發行版。

## 你會拿到什麼

這個目標編譯 CLI、CGI 與 FPM。`php-cli` 是命令列執行檔。`php-cgi` 是 CGI 執行檔。`php-fpm` 是 FastCGI 程序管理器。`phpdbg` 未納入。

FPM 不含 systemd、POSIX ACL 與 AppArmor 整合。設定檔沒有內嵌。未指定 `-y` 時，`php-fpm` 讀取 `/usr/local/etc/php-fpm.conf`。`php-fpm -y /path/to/php-fpm.conf` 可以改用其他檔案。在舊主機上怎麼啟動，見 [在舊主機執行](../running-on-old-hosts.md)。

這個目標的 `php -m` 包含 `bcmath`、`bz2`、`calendar`、`curl`、`exif`、`ftp`、`gd`（FreeType 與 JPEG）、`intl`、`mbstring`、`mysqli`、`mysqlnd`、`openssl`、`pcntl`、`pdo_mysql`、`pdo_sqlite`、`sockets`、`sodium`、`sqlite3`、`xml`、`xsl`、`zip`、`zlib`。MySQL 使用 `mysqlnd`。

PHP 裡的 curl 擴充，用的是另一份較小的靜態 libcurl，和 [curl](curl.md) 目標不同。這份 libcurl 未包含 HTTP/2、Brotli、zstd、IDN 與 Public Suffix List。

執行檔不含 `php.ini`，也不含 CA 憑證包。行程需要設定時，加上 `-c /path/to/php.ini`。OpenSSL 仍會讀取主機的憑證庫；ini 裡的 `openssl.cafile` 可以改指其他憑證包。

編譯完成後，`dist/php/VERSION` 寫的是解析後的 `x.y.z`。`php-cli -v`、`php-cgi -v` 與 `php-fpm -v` 會回報同一個版本。
