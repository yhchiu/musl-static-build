# PHP

[中文](../zh-TW/targets/php.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh php              # latest 8.5.x
./build-static.sh php 8.4          # latest 8.4.x
./build-static.sh php 8.5.11       # that exact release
```

| | |
|--|--|
| Default | `8.5`, resolved to the newest `8.5.x` tarball before the build |
| Alpine | 3.20 |
| Output | `dist/php/php-cli`, `dist/php/php-cgi`, `dist/php/php-fpm` |
| Checked | `8.5.11` on x86_64. The three binaries are static, they report 8.5.11, and `php-fpm` answered one FastCGI request. `8.4` was built and exercised earlier; its exact patch number was not recorded. |

`x.y` is resolved through the [PHP releases API](https://www.php.net/releases/index.php?json&version=8.5) from an Alpine container. `x.y.z` downloads that release as given.

## What you get

This target builds the CLI, CGI, and FPM SAPIs. `php-cli` is the CLI binary. `php-cgi` is the CGI binary. `php-fpm` is the FastCGI process manager. `phpdbg` is left out.

FPM is built without systemd, POSIX ACL, and AppArmor integration. The config file is not embedded. With no `-y`, `php-fpm` reads `/usr/local/etc/php-fpm.conf`. Pass `-y /path/to/php-fpm.conf` to select another file. How to run it on an old host is in [Run it on an old host](../running-on-old-hosts.md).

`php -m` for this target includes `bcmath`, `bz2`, `calendar`, `curl`, `exif`, `ftp`, `gd` (FreeType and JPEG), `intl`, `mbstring`, `mysqli`, `mysqlnd`, `openssl`, `pcntl`, `pdo_mysql`, `pdo_sqlite`, `sockets`, `sodium`, `sqlite3`, `xml`, `xsl`, `zip`, and `zlib`. MySQL support uses `mysqlnd`.

The curl extension inside PHP is a separate, smaller static libcurl than the [curl](curl.md) target. That copy is built without HTTP/2, Brotli, zstd, IDN, and the Public Suffix List.

The binary does not contain a `php.ini` or a CA bundle. Pass `-c /path/to/php.ini` when the process needs settings. OpenSSL still reads the host certificate store; `openssl.cafile` in the ini selects another bundle.

After a build, `dist/php/VERSION` holds the resolved `x.y.z` release. `php-cli -v`, `php-cgi -v`, and `php-fpm -v` report that same release.
