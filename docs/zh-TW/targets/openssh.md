# OpenSSH

[English](../../targets/openssh.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh openssh
./build-static.sh openssh 8.9p1
./build-static.sh openssh 10.6p1
./build-static.sh openssh 9.9p2 --clean
```

| | |
|--|--|
| 預設 | `9.9p2` |
| 輸出 | `dist/openssh/` |
| 已實測 | x86_64 上的 `9.9p2` 與 `10.6p1`。用戶端與伺服器執行檔都是靜態連結，`ssh -V` 會回報版本。 |

接受的版本是 `8.xpN`、`9.xpN` 與 `10.xpN`。

## 檔案

每次編譯都會匯出：

`ssh`、`scp`、`sftp`、`ssh-keygen`、`ssh-keyscan`、`ssh-add`、`ssh-agent`、`sshd`、`sftp-server`

OpenSSH **9.8** 起另外匯出 `sshd-session`。OpenSSH **10.0** 起另外匯出 `sshd-auth`。較早的版本把這段工作留在 `sshd` 裡，所以那些額外檔案會刻意不出現。

## 寫進 sshd 的路徑

| 設定 | 路徑 |
|------|------|
| 設定檔 | `/etc/ssh/sshd_config` |
| 輔助程式 | `/usr/libexec`（`sftp-server`，以及該版本才有的 `sshd-session`／`sshd-auth`） |
| 權限分離 | 使用者 `sshd`、目錄 `/var/empty` |

用戶端工具不依賴這些路徑。`sshd` 會。啟動 daemon 之前，請把輔助程式複製到 `/usr/libexec/`。

## 這個目標怎麼編譯

| OpenSSH | Alpine | TLS 函式庫 |
|---------|--------|------------|
| 8.x | 3.16 | OpenSSL 1.1。OpenSSH 8.x 不接受 OpenSSL 3。 |
| 9.x 與 10.x | 3.20 | OpenSSL 3 |

這個目標同時連結 zlib。未納入 PAM、SELinux、Kerberos、libedit 與 ldns，並關閉 utmp、wtmp 與 lastlog。sandbox 設為 `none`，以避免靜態執行檔的 seccomp 問題。匯出的檔案不含 host-based 認證、PKCS#11 與 security key 輔助程式。

原始碼 tarball 來自 OpenBSD 的 portable OpenSSH 發行目錄。
