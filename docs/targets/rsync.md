# rsync

[中文](../zh-TW/targets/rsync.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh rsync
./build-static.sh rsync 3.4.1
./build-static.sh rsync 3.5.1 --clean
```

| | |
|--|--|
| Default | `3.5.1` |
| Alpine | 3.20 |
| Output | `dist/rsync/rsync` |
| Accepted versions | `3.x.y` |
| Checked | `3.5.1` on x86_64: static link, `--version`, and one local file copy |

This target statically links OpenSSL, zlib, xxHash, zstd, and lz4. zlib, zstd, and lz4 come from Alpine's static packages. Alpine 3.20 has no static xxHash package, so this target builds xxHash 0.8.3 from source. popt is the copy included with rsync. ACL, xattrs, iconv, and IDN stay off. `rsync-ssl` is a script, so it is not exported.

Tarballs come from the [rsync download directory](https://download.samba.org/pub/rsync/).

## Copy files

```bash
/opt/static/rsync/rsync -a /src/ /dest/
```

Daemon mode reads `/etc/rsyncd.conf` unless you pass `--config`. The usual use of this binary is the client.
