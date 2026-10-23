# nginx

[English](../../targets/nginx.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh nginx
./build-static.sh nginx 1.30.6 --clean
```

| | |
|--|--|
| 預設 | `1.30.6`（stable 分支） |
| Alpine | 3.20 |
| 輸出 | `dist/nginx/nginx` |
| 接受的版本 | 完整 `1.x.y`，從 1.26.0 起；其他版本仍需各自建置驗證 |
| 已實測 | x86_64 上的 `1.30.6`：靜態連結、版本與建置選項、HTTP、反向代理、rewrite、驗證子請求、status、gzip／靜態 gzip、Brotli、PHP-FPM、TLS 1.2／1.3 HTTPS，以及 HTTP/2 SETTINGS 交換 |

這個 target 讓既有 nginx 服務能取得安全與 TLS 更新，而不必升級主機的 glibc 或 OpenSSL。執行檔靜態連結 OpenSSL、PCRE2、zlib、libxml2、libxslt／libexslt 及其相依套件。原始碼來自 [nginx.org](https://nginx.org/en/download.html)。

## 內建模組

這個目標保留 nginx 預設 HTTP 模組，並加入下列選用模組。全部直接編入執行檔，不要使用 `load_module`，也不能載入發行版提供的 `.so` 模組。`nginx -V` 顯示建置選項，不是所有預設模組的完整清單。

| 類別 | 包含功能 |
|------|----------|
| TLS 與協定 | HTTPS、HTTP/2、HTTP/3／QUIC、gRPC |
| 應用程式與代理 | HTTP 反向代理／快取、WebSocket upgrade 轉送、FastCGI（PHP-FPM）、uwsgi、SCGI、memcached、upstream 負載平衡與 keepalive |
| 靜態網站與路由 | 靜態檔案、index／autoindex、try_files、rewrite／redirect、map、geo、split_clients、referer、random index |
| 存取控制與觀測 | Basic authentication、IP 存取規則、auth_request、realip、secure_link、limit_req、limit_conn、stub_status、存取日誌 |
| 壓縮 | gzip、gzip_static、gunzip、Brotli filter、brotli_static |
| 內容處理 | SSI、sub_filter、addition、XSLT、charset、headers、range、slice、mirror、FLV／MP4 pseudo-streaming |
| WebDAV | 內建 PUT、DELETE、MKCOL、COPY、MOVE；不含 PROPFIND／LOCK，並非完整 WebDAV 伺服器 |
| TCP／UDP | stream proxy、SSL termination、realip、ssl_preread、存取控制、連線限制、map／geo、upstream 負載平衡 |
| I/O | Thread pools、file AIO、PCRE JIT；實際使用仍受主機核心與 CPU 能力限制 |

Brotli 採用 [google/ngx_brotli](https://github.com/google/ngx_brotli)，固定於 `a71f9312c2deb28875acc7bacfdd5695a111aa53`，包含該提交固定的 Brotli 子模組。建置不使用 `-march=native`。

未納入：image_filter（需要 libgd 與圖片編解碼相依套件）、GeoIP 資料庫模組、mail proxy、Perl、Lua／OpenResty、njs、ModSecurity 及其他第三方模組。內建 `geo` 模組有包含，不需要 GeoIP 資料庫。這個 musl 靜態執行檔無法載入動態語言模組或外部 OpenSSL provider／engine `.so`。

HTTP/3 已編入，但測試尚未涵蓋實際 QUIC 握手。使用時需要 QUIC listener、憑證與 UDP 存取；early data 支援取決於 TLS 函式庫。HTTP/2 已實測 TLS／ALPN 與 SETTINGS 交換。詳見[上游 HTTP/3 說明](https://nginx.org/en/docs/http/ngx_http_v3_module.html)。

## 主機設定

預設讀取 `/etc/nginx/nginx.conf`。設定檔、MIME 表、CA 憑證包、憑證與私鑰都沒有內嵌或匯出。可用 `-c /絕對路徑/nginx.conf` 指定其他檔案。編入的 prefix 是 `/var/lib/nginx`；`-p` 只改變相對路徑的基準，不會改掉下列絕對暫存路徑。

啟動前建立目錄：

```bash
mkdir -p /etc/nginx /var/www/html /var/log/nginx \
  /var/lib/nginx/client_body /var/lib/nginx/proxy /var/lib/nginx/fastcgi \
  /var/lib/nginx/uwsgi /var/lib/nginx/scgi
```

以下是由 root 啟動 master 的最小 `/etc/nginx/nginx.conf`：

```nginx
user nobody nogroup;  # 改成主機已有的帳號／群組；部分主機是 nobody/nobody。
worker_processes auto;
pid /var/run/nginx.pid;
error_log /var/log/nginx/error.log;
events { worker_connections 1024; }
http {
    types { text/html html; text/css css; application/javascript js; }
    default_type application/octet-stream;
    access_log /var/log/nginx/access.log;
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;
    brotli on;
    brotli_types text/plain text/css application/javascript application/json;
    server {
        listen 8080;
        server_name localhost;
        root /var/www/html;
        index index.html;
        location / { try_files $uri $uri/ =404; }
    }
}
```

```bash
/opt/static/nginx/nginx -t
/opt/static/nginx/nginx -g 'daemon off;'
```

非 root 啟動時，必須把 PID、日誌與五種 `*_temp_path` 都改成可寫入的路徑，並省略 `user`。HTTPS 需要 `listen 443 ssl;`、`ssl_certificate` 與 `ssl_certificate_key`；HTTP/2 用 `http2 on;` 啟用。連接 HTTPS upstream 時，明確設定信任來源：`proxy_ssl_verify on; proxy_ssl_trusted_certificate /path/to/ca-bundle.crt; proxy_ssl_server_name on;`。

搭配本專案的 PHP-FPM 時，在 `server` 加入以下設定，並使用 FPM pool 設定的通訊埠。FPM 必須另外啟動，nginx 本身不執行 PHP。

```nginx
location ~ \.php$ {
    try_files $uri =404;
    fastcgi_pass 127.0.0.1:9000;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    fastcgi_param SCRIPT_NAME $fastcgi_script_name;
    fastcgi_param QUERY_STRING $query_string;
    fastcgi_param REQUEST_METHOD $request_method;
    fastcgi_param CONTENT_TYPE $content_type;
    fastcgi_param CONTENT_LENGTH $content_length;
    fastcgi_param REQUEST_URI $request_uri;
    fastcgi_param SERVER_PROTOCOL $server_protocol;
    fastcgi_param REMOTE_ADDR $remote_addr;
    fastcgi_param SERVER_NAME $server_name;
    fastcgi_param SERVER_PORT $server_port;
    fastcgi_param HTTPS $https if_not_empty;
    fastcgi_param REDIRECT_STATUS 200;
}
```

WebSocket 代理另外需要 `proxy_http_version 1.1`，並明確轉送 `Upgrade`／`Connection` 標頭。模組編入後仍須透過設定啟用對應功能。
