# Apache httpd

[English](../../targets/apache.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh apache
./build-static.sh apache 2.4.62
./build-static.sh apache 2.4.69 --clean
```

| | |
|--|--|
| 預設 | `2.4.69` |
| Alpine | 3.20 |
| 輸出 | `dist/apache/httpd`、`dist/apache/httpd-prefork`、`dist/apache/htpasswd` |
| 接受的版本 | `2.4.x`，從 2.4.53 起（這些版本需要 PCRE2） |
| 已實測 | x86_64 上的 `2.4.69`。三個執行檔都是靜態連結，`httpd -v` 與 `httpd-prefork -v` 回報 2.4.69，兩台伺服器各成功回應一次 HTTP 請求。 |

`httpd`、`httpd-prefork` 與 `htpasswd` 靜態連結 APR 1.7.6、APR-util 1.6.5、OpenSSL、zlib、PCRE2、nghttp2、Brotli 與 Expat。`httpd` 使用 **event** MPM。`httpd-prefork` 使用 **prefork** MPM。每個 2.4.x 編譯都固定使用這兩個 APR 版本。`httpd -V` 會印出它們。

Tarball 來自 [Apache 封存](https://archive.apache.org/dist/httpd/)。

## 主機上的設定

模組直接編譯進 `httpd` 與 `httpd-prefork`。這個目標未包含 `mod_so`，所以這兩個執行檔無法在執行時載入 `.so`。設定檔不要寫 `LoadModule`。同一份設定檔可以給兩台伺服器使用。HTTP/2 要用 event 的 `httpd`。

編譯時寫入的預設設定檔是 `/etc/httpd/httpd.conf`。預設 MIME 檔是 `/etc/httpd/mime.types`。這兩個檔案都不會內嵌。`httpd -f /path/to/httpd.conf` 可以改用其他設定，設定裡的 `TypesConfig` 也可以改指其他 MIME 檔。

`User` 與 `Group` 必須是這台機器上存在的非 root 帳號。一份最短設定寫在 [在舊主機執行](../running-on-old-hosts.md)。

`mod_dbd` 只有 DBD 框架。MySQL、PostgreSQL 與 SQLite 驅動未連結。`mod_socache_memcache` 與 `mod_socache_redis` 會連到外部伺服器；那些伺服器不在這個目標裡。

## 2.4.69 內建的模組

以下是已實測的 2.4.69 event 版以 `httpd -l` 回報的清單。`httpd-prefork -l` 是同一份清單，只把 `event` 換成 `prefork`、把 `mod_cgid` 換成 `mod_cgi`：

- 核心與 MPM：`core`、`http_core`、`event`、`mod_unixd`
- 認證與授權：`mod_authn_file`、`mod_authn_dbm`、`mod_authn_anon`、`mod_authn_dbd`、`mod_authn_socache`、`mod_authn_core`、`mod_authz_host`、`mod_authz_groupfile`、`mod_authz_user`、`mod_authz_dbm`、`mod_authz_owner`、`mod_authz_dbd`、`mod_authz_core`、`mod_access_compat`、`mod_auth_basic`、`mod_auth_form`、`mod_auth_digest`、`mod_allowmethods`
- 快取：`mod_file_cache`、`mod_cache`、`mod_cache_disk`、`mod_cache_socache`、`mod_socache_shmcb`、`mod_socache_dbm`、`mod_socache_memcache`、`mod_socache_redis`
- 過濾器：`mod_buffer`、`mod_ratelimit`、`mod_reqtimeout`、`mod_ext_filter`、`mod_request`、`mod_include`、`mod_filter`、`mod_substitute`、`mod_sed`、`mod_deflate`、`mod_brotli`
- HTTP、日誌與中繼資料：`mod_mime`、`mod_log_config`、`mod_log_debug`、`mod_logio`、`mod_env`、`mod_expires`、`mod_headers`、`mod_unique_id`、`mod_setenvif`、`mod_version`、`mod_remoteip`
- 代理：`mod_proxy`、`mod_proxy_connect`、`mod_proxy_ftp`、`mod_proxy_http`、`mod_proxy_fcgi`、`mod_proxy_scgi`、`mod_proxy_uwsgi`、`mod_proxy_fdpass`、`mod_proxy_wstunnel`、`mod_proxy_ajp`、`mod_proxy_balancer`、`mod_proxy_express`、`mod_proxy_hcheck`、`mod_proxy_http2`、`mod_lbmethod_byrequests`、`mod_lbmethod_bytraffic`、`mod_lbmethod_bybusyness`、`mod_lbmethod_heartbeat`、`mod_heartbeat`、`mod_heartmonitor`、`mod_slotmem_shm`、`mod_watchdog`
- TLS 與 HTTP/2：`mod_ssl`、`mod_http2`
- WebDAV：`mod_dav`、`mod_dav_fs`、`mod_dav_lock`
- 對應與內容：`mod_vhost_alias`、`mod_negotiation`、`mod_dir`、`mod_actions`、`mod_speling`、`mod_userdir`、`mod_alias`、`mod_rewrite`、`mod_status`、`mod_autoindex`、`mod_info`、`mod_cgid`、`mod_session`、`mod_session_cookie`、`mod_session_dbd`、`mod_macro`、`mod_dbd`、`mod_dumpio`

這個目標未編譯進去的模組：

- `mod_so`：完全靜態的 musl 執行檔無法在執行時載入模組
- `mod_md`（需要 jansson 與 libcurl）、`mod_lua`、`mod_ldap`、`mod_authnz_ldap`
- `mod_session_crypto`：APR-util 未啟用 crypto
- `httpd` 不含 `mod_cgi`：event MPM 使用 `mod_cgid`
- `httpd-prefork` 不含 `mod_cgid`：prefork MPM 使用 `mod_cgi`
- `mod_proxy_html` 與 `mod_xml2enc`：需要 libxml2
- `mod_log_forensic`、`mod_suexec` 與範例模組
