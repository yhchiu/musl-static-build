# nginx

[中文](../zh-TW/targets/nginx.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh nginx
./build-static.sh nginx 1.30.6 --clean
```

| | |
|--|--|
| Default | `1.30.6` (stable branch) |
| Alpine | 3.20 |
| Output | `dist/nginx/nginx` |
| Accepted versions | Exact `1.x.y`, from 1.26.0 upward; other releases need their own build checks |
| Checked | `1.30.6` on x86_64: static link, version and build options, HTTP, reverse proxy, rewrite, auth subrequests, status, gzip/static gzip, Brotli, PHP-FPM, HTTPS with TLS 1.2/1.3, and an HTTP/2 SETTINGS exchange |

This target lets an existing nginx installation receive security and TLS updates without upgrading the host's glibc or OpenSSL. It links OpenSSL, PCRE2, zlib, libxml2, libxslt/libexslt and their static dependencies. Tarballs come from [nginx.org](https://nginx.org/en/download.html).

## Built-in modules

This target retains nginx's default HTTP modules and adds the optional modules below. All are linked into the executable; do not use `load_module` or copy distribution `.so` modules alongside it. `nginx -V` prints build options, not a complete list of default modules.

| Area | Included functionality |
|------|------------------------|
| TLS and protocols | HTTPS, HTTP/2, HTTP/3/QUIC, gRPC |
| Applications and proxying | HTTP reverse proxy/cache, WebSocket upgrade forwarding, FastCGI (PHP-FPM), uwsgi, SCGI, memcached, upstream load balancing and keepalive |
| Static sites and routing | Static files, index/autoindex, `try_files`, rewrite/redirects, map, geo, split_clients, referer, random index |
| Access and observability | Basic authentication, IP access rules, auth_request, realip, secure_link, limit_req, limit_conn, stub_status, access logs |
| Compression | gzip, gzip_static, gunzip, Brotli filter and brotli_static |
| Content | SSI, sub_filter, addition, XSLT, charset, headers, ranges, slice, mirror, FLV/MP4 pseudo-streaming |
| WebDAV | Built-in PUT, DELETE, MKCOL, COPY and MOVE; not a full WebDAV server with PROPFIND/LOCK |
| TCP/UDP | stream proxy, SSL termination, realip, ssl_preread, access rules, connection limits, map/geo and upstream balancing |
| I/O | Thread pools, file AIO and PCRE JIT; their use still depends on host kernel/CPU capabilities |

Brotli uses [google/ngx_brotli](https://github.com/google/ngx_brotli) pinned at `a71f9312c2deb28875acc7bacfdd5695a111aa53`, including its pinned Brotli submodule. Builds do not use `-march=native`.

Left out: image_filter (libgd and image codec dependencies), GeoIP database modules, mail proxy, Perl, Lua/OpenResty, njs, ModSecurity, and other third-party modules. The built-in `geo` module is included and does not need a GeoIP database. Dynamic language modules and external OpenSSL provider/engine `.so` files cannot be loaded by this static musl executable.

HTTP/3 is compiled in but its network handshake has not been tested by this suite. It needs a QUIC listener, a certificate and UDP access; early-data support depends on the TLS library. HTTP/2 has an actual TLS/ALPN and SETTINGS check. See the [upstream HTTP/3 notes](https://nginx.org/en/docs/http/ngx_http_v3_module.html).

## Host configuration

The default configuration is `/etc/nginx/nginx.conf`. No configuration, MIME table, CA bundle, certificate or private key is embedded or exported. Use `-c /absolute/path/nginx.conf` for another file. The compiled prefix is `/var/lib/nginx`; `-p` changes relative paths, but not the absolute temporary paths below.

Create the directories before starting:

```bash
mkdir -p /etc/nginx /var/www/html /var/log/nginx \
  /var/lib/nginx/client_body /var/lib/nginx/proxy /var/lib/nginx/fastcgi \
  /var/lib/nginx/uwsgi /var/lib/nginx/scgi
```

A minimal `/etc/nginx/nginx.conf` for a root-started master:

```nginx
user nobody nogroup;  # Use an existing user/group; some hosts use nobody/nobody.
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

An unprivileged launch must override the PID, logs and all five `*_temp_path` directives with writable paths and omit `user`. HTTPS needs `listen 443 ssl;`, `ssl_certificate` and `ssl_certificate_key`; enable HTTP/2 with `http2 on;`. Configure trust explicitly for HTTPS upstreams: `proxy_ssl_verify on; proxy_ssl_trusted_certificate /path/to/ca-bundle.crt; proxy_ssl_server_name on;`.

For this project's PHP-FPM, add the following inside `server` and use the port configured in the FPM pool. FPM must be running separately; nginx does not execute PHP itself.

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

WebSocket proxying additionally needs `proxy_http_version 1.1` and explicit `Upgrade`/`Connection` forwarding. Enabling a module does not automatically enable its configuration directives.
