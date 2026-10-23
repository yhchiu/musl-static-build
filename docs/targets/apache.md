# Apache httpd

[中文](../zh-TW/targets/apache.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh apache
./build-static.sh apache 2.4.62
./build-static.sh apache 2.4.69 --clean
```

| | |
|--|--|
| Default | `2.4.69` |
| Alpine | 3.20 |
| Output | `dist/apache/httpd`, `dist/apache/httpd-prefork`, `dist/apache/htpasswd` |
| Accepted versions | `2.4.x`, from 2.4.53 upward (these releases need PCRE2) |
| Checked | `2.4.69` on x86_64. All three binaries are static, `httpd -v` and `httpd-prefork -v` report 2.4.69, and each server answered one HTTP request. |

`httpd`, `httpd-prefork`, and `htpasswd` statically link APR 1.7.6, APR-util 1.6.5, OpenSSL, zlib, PCRE2, nghttp2, Brotli, and Expat. `httpd` uses the **event** MPM. `httpd-prefork` uses the **prefork** MPM. APR and APR-util stay pinned for every 2.4.x build. `httpd -V` reports those APR versions.

Tarballs come from the [Apache archive](https://archive.apache.org/dist/httpd/).

## Config on the host

Modules are compiled into `httpd` and `httpd-prefork`. `mod_so` is left out, so these binaries cannot load a `.so` at runtime. Leave `LoadModule` out of the configuration. The same config file works for both servers. HTTP/2 needs the event binary, `httpd`.

The compiled-in default config is `/etc/httpd/httpd.conf`. The compiled-in MIME file is `/etc/httpd/mime.types`. Neither file is embedded. `httpd -f /path/to/httpd.conf` selects another config, and `TypesConfig` inside it can point at another MIME file.

`User` and `Group` must name a non-root account that exists on the machine. A minimal config is in [Run on an old host](../running-on-old-hosts.md).

`mod_dbd` is the DBD framework only. MySQL, PostgreSQL, and SQLite drivers are left unlinked. `mod_socache_memcache` and `mod_socache_redis` speak to external servers; those servers are not part of this target.

## Modules compiled into 2.4.69

This is the list `httpd -l` reported for the checked 2.4.69 event build. `httpd-prefork -l` is the same list with `prefork` in place of `event` and `mod_cgi` in place of `mod_cgid`:

- Core and MPM: `core`, `http_core`, `event`, `mod_unixd`
- Authentication: `mod_authn_file`, `mod_authn_dbm`, `mod_authn_anon`, `mod_authn_dbd`, `mod_authn_socache`, `mod_authn_core`, `mod_authz_host`, `mod_authz_groupfile`, `mod_authz_user`, `mod_authz_dbm`, `mod_authz_owner`, `mod_authz_dbd`, `mod_authz_core`, `mod_access_compat`, `mod_auth_basic`, `mod_auth_form`, `mod_auth_digest`, `mod_allowmethods`
- Cache: `mod_file_cache`, `mod_cache`, `mod_cache_disk`, `mod_cache_socache`, `mod_socache_shmcb`, `mod_socache_dbm`, `mod_socache_memcache`, `mod_socache_redis`
- Filters: `mod_buffer`, `mod_ratelimit`, `mod_reqtimeout`, `mod_ext_filter`, `mod_request`, `mod_include`, `mod_filter`, `mod_substitute`, `mod_sed`, `mod_deflate`, `mod_brotli`
- HTTP, logging, and metadata: `mod_mime`, `mod_log_config`, `mod_log_debug`, `mod_logio`, `mod_env`, `mod_expires`, `mod_headers`, `mod_unique_id`, `mod_setenvif`, `mod_version`, `mod_remoteip`
- Proxy: `mod_proxy`, `mod_proxy_connect`, `mod_proxy_ftp`, `mod_proxy_http`, `mod_proxy_fcgi`, `mod_proxy_scgi`, `mod_proxy_uwsgi`, `mod_proxy_fdpass`, `mod_proxy_wstunnel`, `mod_proxy_ajp`, `mod_proxy_balancer`, `mod_proxy_express`, `mod_proxy_hcheck`, `mod_proxy_http2`, `mod_lbmethod_byrequests`, `mod_lbmethod_bytraffic`, `mod_lbmethod_bybusyness`, `mod_lbmethod_heartbeat`, `mod_heartbeat`, `mod_heartmonitor`, `mod_slotmem_shm`, `mod_watchdog`
- TLS and HTTP/2: `mod_ssl`, `mod_http2`
- WebDAV: `mod_dav`, `mod_dav_fs`, `mod_dav_lock`
- Mapping and content: `mod_vhost_alias`, `mod_negotiation`, `mod_dir`, `mod_actions`, `mod_speling`, `mod_userdir`, `mod_alias`, `mod_rewrite`, `mod_status`, `mod_autoindex`, `mod_info`, `mod_cgid`, `mod_session`, `mod_session_cookie`, `mod_session_dbd`, `mod_macro`, `mod_dbd`, `mod_dumpio`

Left out of this target:

- `mod_so`, because a fully static musl binary cannot load modules at runtime
- `mod_md` (it needs jansson and libcurl), `mod_lua`, `mod_ldap`, `mod_authnz_ldap`
- `mod_session_crypto`, because APR-util is built without crypto
- `mod_cgi` from `httpd`, because the event MPM uses `mod_cgid`
- `mod_cgid` from `httpd-prefork`, because the prefork MPM uses `mod_cgi`
- `mod_proxy_html` and `mod_xml2enc`, because they need libxml2
- `mod_log_forensic`, `mod_suexec`, and the example modules
