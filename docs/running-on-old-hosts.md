# Run the binaries on an old Linux host

[中文](zh-TW/running-on-old-hosts.md) · [Back to the README](../README.md)

The build machine and the old host are different jobs. Docker runs on the build machine. The old host only receives the finished files.

## 1. Match the CPU architecture

The binary matches the machine that runs Docker. An x86_64 build runs on x86_64 hosts. Copy it to a host with that same architecture.

## 2. Copy the directory

From the build machine, with `dist/curl/` as the example:

```bash
scp -r dist/curl oldhost:/opt/static/
ssh oldhost /opt/static/curl/curl --version
```

On the old host, `file` should still report `statically linked`. `ldd` should report `not a dynamic executable`. Some very old `file` builds only say `ELF` and `executable`; `ldd` is the clearer check there.

Call the program by its path, or add that directory to `PATH`. Replacing the distro's `/usr/bin/curl` is optional. Keeping the static file under `/opt/static/` leaves the original package in place.

## 3. Give each program the files it still reads

Static linking covers the libraries. Configuration, CA certificates, and a few helper programs stay on the host.

### curl

```bash
/opt/static/curl/curl --version
/opt/static/curl/curl --fail --location https://example.com/ -o /dev/null
```

HTTPS reads `/etc/ssl/certs/ca-certificates.crt` or `/etc/ssl/certs`. When the host keeps its bundle somewhere else:

```bash
/opt/static/curl/curl --cacert /path/to/ca-bundle.crt https://example.com/
```

`CURL_CA_BUNDLE` selects the same file. Features and the protocols this target leaves out: [curl](targets/curl.md).

### wget

```bash
/opt/static/wget/wget --version
/opt/static/wget/wget -O /dev/null https://example.com/
```

HTTPS uses OpenSSL's default locations, `/etc/ssl/cert.pem` and `/etc/ssl/certs`, and honors `SSL_CERT_FILE` and `SSL_CERT_DIR`. Another bundle can be passed per command:

```bash
/opt/static/wget/wget --ca-certificate /path/to/ca-bundle.crt https://example.com/
```

Details: [wget](targets/wget.md).

### PHP

`php-cli` is the command-line program. `php-cgi` is the CGI program. `php-fpm` is the FastCGI process manager.

```bash
/opt/static/php/php-cli -v
/opt/static/php/php-cli -m
```

The build does not ship a `php.ini`. Pass one when you need it:

```bash
/opt/static/php/php-cli -c /etc/php.ini -v
```

`php-fpm` keeps its configuration on the host. With no `-y`, it reads `/usr/local/etc/php-fpm.conf`. `user` and `group` in the pool must name an account that exists on the machine. Start it as root so the workers can switch to that account, and start it by the absolute path of the binary.

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

`group = nobody` applies to some distributions. Others use `nogroup`. Use a group that exists on that host. The account that runs the web server needs to be able to connect to the socket. Create the log directory, the PID directory, and the socket directory before starting:

```bash
/opt/static/php/php-fpm -y /etc/php-fpm.conf -t
/opt/static/php/php-fpm -y /etc/php-fpm.conf -F
```

`-F` keeps the process in the foreground. Omit `-F` to run in the background; the PID is written to the `pid` path. Pass `-c /etc/php.ini` when the workers need ini settings. The pool accepts script names that end in `.php`.

This project's `httpd` includes `mod_proxy_fcgi`. A handler that uses the same socket:

```apache
<FilesMatch "\.php$">
    SetHandler "proxy:unix:/var/run/php-fpm.sock|fcgi://localhost"
</FilesMatch>
```

Extensions and the curl extension's limits: [PHP](targets/php.md).

### OpenSSH

Client programs (`ssh`, `scp`, `sftp`, `ssh-keygen`, `ssh-keyscan`, `ssh-add`, `ssh-agent`) run from any directory:

```bash
/opt/static/openssh/ssh -V
/opt/static/openssh/ssh user@other-host
```

`sshd` is different. It always looks in the paths compiled into the binary:

| File from `dist/openssh/` | Where `sshd` looks |
|---------------------------|--------------------|
| `sftp-server` | `/usr/libexec/sftp-server` |
| `sshd-session` (OpenSSH 9.8 and later) | `/usr/libexec/sshd-session` |
| `sshd-auth` (OpenSSH 10.0 and later) | `/usr/libexec/sshd-auth` |
| config | `/etc/ssh/sshd_config` |

Copy those helpers to `/usr/libexec/` before starting `sshd`. Leaving them next to `sshd` in `/opt/static/openssh/` does not change the lookup. Privilege separation uses the user `sshd` and the directory `/var/empty`.

This target leaves out PAM, Kerberos, SELinux, host-based authentication, PKCS#11, and security-key helpers. Host keys and `authorized_keys` still work. Create missing host keys with the static `ssh-keygen` if the machine does not already have them.

Version-specific files and the Alpine/OpenSSL choice: [OpenSSH](targets/openssh.md).

### Apache httpd

`httpd`, `httpd-prefork`, and `htpasswd` are the three binaries. `httpd` is the event MPM. `httpd-prefork` is the prefork MPM. Modules are compiled into both servers, so a config for either binary has no `LoadModule` lines. The same config works for both. HTTP/2 needs `httpd`. Start one server at a time when they share a `Listen` port.

The default config path is `/etc/httpd/httpd.conf`, and the default MIME file is `/etc/httpd/mime.types`. `httpd -f` selects another config. `User` and `Group` must name a non-root account that exists on the machine. Starting the server this way needs root so httpd can switch to that account.

A short config that serves one directory, matching the shape used by the project's HTTP check:

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

`/etc/httpd/mime.types` can be a small file, for example a line `text/html html`. Create the document root, the log file's directory, and the PID file's directory before starting:

```bash
/opt/static/apache/httpd -f /etc/httpd/httpd.conf -t
/opt/static/apache/httpd -f /etc/httpd/httpd.conf -DFOREGROUND
/opt/static/apache/httpd-prefork -f /etc/httpd/httpd.conf -DFOREGROUND
```

`Group nobody` matches some distributions. Others use `nogroup`. Use the group that exists on that host.

`htpasswd` only needs a filename:

```bash
/opt/static/apache/htpasswd -nb user secret
```

The module list, and what `mod_dbd` can and cannot reach: [Apache httpd](targets/apache.md).

## rsync

Copy `dist/rsync/rsync` to the old host. A local copy does not need extra files:

```bash
/opt/static/rsync/rsync -a /src/ /dest/
```

`rsync --daemon` reads `/etc/rsyncd.conf` unless you pass `--config`. ACL, xattrs, iconv, and IDN are not in this build.

## openssl

Copy `dist/openssl/openssl` to the old host. It does not contain a CA bundle. Certificate checks use `/etc/ssl/cert.pem` and `/etc/ssl/certs`, and follow `SSL_CERT_FILE` and `SSL_CERT_DIR`.

```bash
/opt/static/openssl/openssl version
/opt/static/openssl/openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj /CN=localhost
```

Details: [openssl](targets/openssl.md).

## git

Copy the whole `dist/git/` directory and keep the directory name `git`. The helpers have to stay next to the `git` binary. An absolute path then reports that directory from `git --exec-path`.

```bash
/opt/static/git/git --version
/opt/static/git/git --exec-path
```

`git init` creates a repository without sample hooks, because this build does not include the template directory. Set a name and email before the first commit:

```bash
/opt/static/git/git config --global user.name "Your Name"
/opt/static/git/git config --global user.email "you@example.com"
```

HTTPS uses `/etc/ssl/cert.pem` and `/etc/ssl/certs`, and follows `SSL_CERT_FILE` and `SSL_CERT_DIR`. The binaries do not contain a CA bundle.

Details: [git](targets/git.md).

## nginx

Copy `dist/nginx/nginx` to the old host. Modules are compiled in; omit `load_module`. The default config is `/etc/nginx/nginx.conf`. Configuration, log/temp directories and certificates remain on the host. Check before starting:

```bash
/opt/static/nginx/nginx -V
/opt/static/nginx/nginx -c /etc/nginx/nginx.conf -t
/opt/static/nginx/nginx -c /etc/nginx/nginx.conf -g 'daemon off;'
```

The compiled worker user/group is `nobody/nobody`; override `user` with an existing account/group, such as `nobody nogroup`. The [nginx guide](targets/nginx.md) provides directory setup, a standalone config, PHP-FPM integration and the module list.

## stunnel

Copy `dist/stunnel/stunnel` to the old host and supply a configuration file. A client must verify both the certificate chain and the peer hostname, using `verifyChain`, `CAfile` and `checkHost`. A server needs its certificate and private key.

```bash
/opt/static/stunnel/stunnel -version
/opt/static/stunnel/stunnel /etc/stunnel/stunnel.conf
```

The [stunnel guide](targets/stunnel.md) includes client/server examples and explains external files and disabled features.
