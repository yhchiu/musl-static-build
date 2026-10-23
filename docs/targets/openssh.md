# OpenSSH

[中文](../zh-TW/targets/openssh.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh openssh
./build-static.sh openssh 8.9p1
./build-static.sh openssh 10.6p1
./build-static.sh openssh 9.9p2 --clean
```

| | |
|--|--|
| Default | `9.9p2` |
| Output | `dist/openssh/` |
| Checked | `9.9p2` and `10.6p1` on x86_64. Client and server binaries are static, and `ssh -V` reports the version. |

Accepted versions are `8.xpN`, `9.xpN`, and `10.xpN`.

## Files

Every build exports:

`ssh`, `scp`, `sftp`, `ssh-keygen`, `ssh-keyscan`, `ssh-add`, `ssh-agent`, `sshd`, `sftp-server`

OpenSSH **9.8** and later also export `sshd-session`. OpenSSH **10.0** and later also export `sshd-auth`. Earlier releases keep that work inside `sshd`, so those extra files are absent on purpose.

## Paths compiled into sshd

| Setting | Path |
|---------|------|
| Config | `/etc/ssh/sshd_config` |
| Helper programs | `/usr/libexec` (`sftp-server`, and `sshd-session` / `sshd-auth` when that release has them) |
| Privilege separation | user `sshd`, directory `/var/empty` |

Client tools do not need those paths. `sshd` does. Copy the helpers into `/usr/libexec/` before you start the daemon.

## How this target is built

| OpenSSH | Alpine | TLS library |
|---------|--------|-------------|
| 8.x | 3.16 | OpenSSL 1.1. OpenSSH 8.x rejects OpenSSL 3. |
| 9.x and 10.x | 3.20 | OpenSSL 3 |

This target also links zlib. It leaves out PAM, SELinux, Kerberos, libedit, and ldns, and it turns off utmp, wtmp, and lastlog. The sandbox is `none`, which avoids seccomp problems in a static binary. Host-based authentication, PKCS#11, and security-key helpers are not part of the export.

Source tarballs come from the OpenBSD portable OpenSSH release directory.
