# git

[中文](../zh-TW/targets/git.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh git
./build-static.sh git 2.47.2
./build-static.sh git 2.56.0 --clean
```

| | |
|--|--|
| Default | `2.56.0` |
| Alpine | 3.20 |
| Output | `dist/git/` (`git` and the helpers listed below) |
| Accepted versions | `2.x.y` |
| Checked | `2.56.0` on x86_64: static link, `--version`, `--exec-path`, and one local commit |

This target builds a small static libcurl (OpenSSL and zlib, without HTTP/2, Brotli, or IDN) in the same image, then builds Git against that libcurl and Alpine's static OpenSSL. It does not use the [openssl](openssl.md) or [curl](curl.md) targets. PCRE2 is enabled. musl has no `REG_STARTEND`, so this target uses Git's bundled regex. Gettext, Perl, Python, Tcl/Tk, and Rust stay off.

`RUNTIME_PREFIX` is on. `bindir` and `gitexecdir` are both the relative path `git`, so the helpers are found when they sit next to `git` in a directory named `git`.

Exported files:

- `git`
- `git-receive-pack`, `git-upload-pack`, `git-upload-archive`
- `git-shell`
- `git-http-backend`
- `git-remote-http`, `git-remote-https`

Shell scripts are not exported. The template directory is not included. `git init` still creates a repository; it does not install sample hooks.

Tarballs come from [kernel.org](https://www.kernel.org/pub/software/scm/git/).

## HTTPS

`git-remote-https` uses the OpenSSL certificate paths `/etc/ssl/cert.pem` and `/etc/ssl/certs`, and follows `SSL_CERT_FILE` and `SSL_CERT_DIR`. The binaries do not contain a CA bundle.
