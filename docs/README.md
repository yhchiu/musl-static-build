# Documentation

[中文文件](zh-TW/README.md)

This directory holds the detail that does not belong on the project front page.

| Guide | Read it when you want to |
|-------|--------------------------|
| [Build and check](usage.md) | Choose a version, pass `--clean` or `--no-test`, and see where files are written |
| [Run on an old host](running-on-old-hosts.md) | Copy a finished build onto a machine that cannot upgrade glibc |
| [PHP](targets/php.md) | See the CLI, CGI, and PHP-FPM build, extensions, and version lookup |
| [OpenSSH](targets/openssh.md) | Install `sshd` and the `/usr/libexec` helpers |
| [curl](targets/curl.md) | Use HTTPS and HTTP/2, and point at a CA bundle |
| [wget](targets/wget.md) | Use HTTPS and point at a CA bundle |
| [rsync](targets/rsync.md) | Copy files with zstd, lz4, and xxHash |
| [OpenSSL](targets/openssl.md) | Run the `openssl` command and point at a CA bundle |
| [Git](targets/git.md) | Use `git` and the HTTPS helpers from one directory |
| [Apache httpd](targets/apache.md) | Write a config with modules already compiled in |
| [nginx](targets/nginx.md) | Use the built-in web/stream modules, Brotli, TLS and PHP-FPM |
| [stunnel](targets/stunnel.md) | Configure TLS client/server forwarding and certificate verification |
| [Add a program](adding-a-target.md) | Add `targets/<name>/` without changing the runner |
| [Development](development.md) | Run the tests, read the layout, and change a target's build |
