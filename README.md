# musl-static-build

This project builds **fully static musl binaries** that can be copied directly to old Linux hosts whose glibc cannot be upgraded. It prioritizes tools whose older versions pose **significant security risks or lack essential functionality or protocol compatibility**, while newer versions are difficult to deploy because of glibc or dependency constraints.

Typical needs include fixing known security vulnerabilities in remote access tools and enabling download tools to use the TLS versions and algorithms required by current services.

Supported programs include **PHP, OpenSSH, curl, wget, rsync, OpenSSL, Git, Apache httpd, nginx, and stunnel**.

A program built on a current distribution often stops on those machines with `GLIBC_2.xx not found`. This project links each program and the libraries it needs into one file, using Alpine Linux and musl inside Docker. The old host keeps its existing system libraries and runs the new file beside them.

Compile on a machine that has Docker. Run the finished files on the old host. The binary uses the CPU architecture of the Docker host. The builds checked so far are x86_64.

中文說明：[README.zh-TW.md](README.zh-TW.md)

## Programs

| Program | Default version | Output |
|---------|-----------------|--------|
| PHP 8.x | `8.5` (latest patch) | `dist/php/php-cli`, `dist/php/php-cgi`, `dist/php/php-fpm` |
| OpenSSH 8.x / 9.x / 10.x | `9.9p2` | `dist/openssh/` (`ssh`, `sshd`, `sftp-server`, …) |
| curl 8.x | `8.22.0` | `dist/curl/curl` |
| wget 1.x | `1.25.0` | `dist/wget/wget` |
| rsync 3.x | `3.5.1` | `dist/rsync/rsync` |
| OpenSSL 3.x | `3.5.9` | `dist/openssl/openssl` |
| Git 2.x | `2.56.0` | `dist/git/` (`git`, `git-remote-https`, …) |
| Apache httpd 2.4.x | `2.4.69` | `dist/apache/httpd`, `dist/apache/httpd-prefork`, `dist/apache/htpasswd` |
| nginx 1.x | `1.30.6` | `dist/nginx/nginx` |
| stunnel 5.x | `5.82` | `dist/stunnel/stunnel` |

The build stops if `file` does not report `statically linked`.

## What the build machine needs

- Docker
- Internet access, to pull the Alpine image and download source
- Bash

The old host does not need Docker or a newer glibc. A kernel that lacks a syscall the program uses can still refuse to run it.

## Build

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

Finished files are written to `dist/<program>/` in the directory where you run the script. `./build-static.sh` prints help. `./build-static.sh --list` prints every target and the version form it accepts.

Pin a release, or rebuild without the Docker cache:

```bash
./build-static.sh php 8.4
./build-static.sh php 8.5.11
./build-static.sh openssh 8.9p1
./build-static.sh curl 8.22.0 --clean
```

Flags, version forms, and the checks that run after a build: [docs/usage.md](docs/usage.md).

## Copy the files to the old host

```bash
scp -r dist/curl oldhost:/opt/static/
ssh oldhost /opt/static/curl/curl --version
```

A few paths are compiled into the binaries, so unpacking `dist/` on the old host is only the first step:

- **curl** and **wget** read CA certificates from the host. The file does not contain a CA bundle.
- **sshd** reads `/etc/ssh/sshd_config` and starts `sftp-server`, `sshd-session`, and `sshd-auth` from `/usr/libexec`.
- **php-fpm** reads `/usr/local/etc/php-fpm.conf` unless you pass `-y`. The pool `user` and `group` must exist on the machine.
- **httpd** reads `/etc/httpd/httpd.conf` unless you pass `-f`. Modules are already compiled in, so the config has no `LoadModule` lines.
- **nginx** reads `/etc/nginx/nginx.conf` unless you pass `-c`. Modules are built in; omit `load_module`. Create the log and temporary directories described in its guide.
- **stunnel** reads `/etc/stunnel/stunnel.conf` or a filename passed on the command line. Supply the configuration, CA bundle, and any certificates/keys separately.

How to lay out each program: [docs/running-on-old-hosts.md](docs/running-on-old-hosts.md).

| Program | What this build includes |
|---------|--------------------------|
| [PHP](docs/targets/php.md) | CLI, CGI, and PHP-FPM, with the usual extensions compiled in |
| [OpenSSH](docs/targets/openssh.md) | Client tools and `sshd` |
| [curl](docs/targets/curl.md) | HTTPS, gzip/deflate, and HTTP/2 |
| [wget](docs/targets/wget.md) | HTTPS, gzip, and regular expressions |
| [rsync](docs/targets/rsync.md) | File copy, with zstd, lz4, and xxHash |
| [OpenSSL](docs/targets/openssl.md) | The `openssl` command, with TLS 1.3 |
| [Git](docs/targets/git.md) | `git` and HTTPS helpers in one directory |
| [Apache httpd](docs/targets/apache.md) | `httpd` (event), `httpd-prefork`, and `htpasswd`, modules compiled in |
| [nginx](docs/targets/nginx.md) | HTTPS, HTTP/2/3, proxy/cache, FastCGI, gzip/Brotli, XSLT, WebDAV and stream modules compiled in |
| [stunnel](docs/targets/stunnel.md) | TLS client/server proxy with certificate verification |

## Builds that have been checked

| Program | Checked versions |
|---------|------------------|
| PHP | `8.5.11` on x86_64; `8.4` (exact patch number was not recorded) |
| OpenSSH | `9.9p2`, `10.6p1` on x86_64 |
| curl | `8.22.0` on x86_64 |
| wget | `1.25.0` on x86_64 |
| rsync | `3.5.1` on x86_64 |
| OpenSSL | `3.5.9` on x86_64 |
| Git | `2.56.0` on x86_64 |
| Apache httpd | `2.4.69` on x86_64 |
| nginx | `1.30.6` on x86_64 |
| stunnel | `5.82` on x86_64 |

The version argument accepts other releases in the same series. This table lists the ones that were actually built and exercised. Details are on each program page.

## Contributing

New targets should meet all of the following criteria:

1. **A clear need to upgrade:** the older version has a significant security issue relevant to actual use, or cannot meet essential functionality or protocol compatibility requirements.
2. **An obstacle to deploying the newer version on old hosts:** glibc or dependency versions prevent straightforward deployment, and no suitable ready-to-run build is available.
3. **A solution this project's build approach can provide:** the program can be built as fully static musl binaries, and the required functionality can be verified.

A tool being widely used, having an old version, or being easy to link statically is not, by itself, a reason to add a target.

- [Add a program](docs/adding-a-target.md)
- [Run the tests](docs/development.md)
- [Documentation index](docs/README.md)
