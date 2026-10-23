# stunnel

[中文](../zh-TW/targets/stunnel.md) · [Run it on an old host](../running-on-old-hosts.md)

```bash
./build-static.sh stunnel
./build-static.sh stunnel 5.82 --clean
```

| | |
|--|--|
| Default | `5.82` |
| Alpine | 3.20 |
| Output | `dist/stunnel/stunnel` |
| Accepted versions | Exact `5.x`; only the checked release is verified with these dependencies |
| Checked | `5.82` on x86_64: static link, version, server-mode TLS 1.2/1.3 forwarding, client-mode TLS with chain/hostname verification, and rejection of a wrong hostname or untrusted certificate |

Use this target when an old stunnel/OpenSSL combination cannot negotiate the TLS required by the peer. It links OpenSSL and its required libraries into the executable; installing this project's separate `openssl` command is not required. Source releases come from [stunnel.org](https://www.stunnel.org/downloads.html), with an archive fallback for old releases.

TCP wrappers (libwrap), systemd socket activation and FIPS support are disabled. This static musl build cannot load external OpenSSL providers or engines. It supports ordinary PEM certificates and keys. It does not export `libstunnel.so` or the legacy `stunnel3` wrapper. CA bundles, private keys and configuration are external.

## Client mode

The default configuration path is `/etc/stunnel/stunnel.conf`; an explicit filename selects another file. This example accepts local plaintext connections on port 1143 and establishes a verified TLS connection to an IMAP server:

```ini
foreground = yes
syslog = no
pid =

[imap]
client = yes
accept = 127.0.0.1:1143
connect = mail.example.com:993
verifyChain = yes
CAfile = /path/to/ca-bundle.crt
checkHost = mail.example.com
sni = mail.example.com
sslVersionMin = TLSv1.2
```

Replace the server name and CA path. Keep `verifyChain` and `checkHost` together: trusting the issuer alone does not check the server's identity. The plaintext listener binds only to loopback. The upstream and the legacy client must still speak the same application protocol; this does not translate application authentication methods.

```bash
/opt/static/stunnel/stunnel -version
/opt/static/stunnel/stunnel /etc/stunnel/stunnel.conf
```

`foreground = yes`, `syslog = no` and an empty `pid` allow this example to run without a service manager or root. To daemonize, select a writable PID path and a logging destination. `setuid` and `setgid`, when used by a root-started service, must name accounts that exist on the host.

## Server mode

To expose a local plaintext service through TLS, use the same global options and replace the service section with:

```ini
[https]
client = no
accept = 0.0.0.0:8443
connect = 127.0.0.1:8080
cert = /path/to/fullchain.pem
key = /path/to/private-key.pem
sslVersionMin = TLSv1.2
```

Provide a certificate for the actual hostname and restrict access to its private key. Configure client-certificate verification separately if mutual TLS is required. See the [upstream HOWTO](https://www.stunnel.org/howto.html).
