# stunnel

[English](../../targets/stunnel.md) · [在舊主機執行](../running-on-old-hosts.md)

```bash
./build-static.sh stunnel
./build-static.sh stunnel 5.82 --clean
```

| | |
|--|--|
| 預設 | `5.82` |
| Alpine | 3.20 |
| 輸出 | `dist/stunnel/stunnel` |
| 接受的版本 | 完整 `5.x`；僅已實測版本確認能搭配此組相依套件 |
| 已實測 | x86_64 上的 `5.82`：靜態連結、版本、server 模式 TLS 1.2／1.3 轉送、client 模式憑證鏈與主機名稱驗證，以及拒絕錯誤主機名稱或不受信任的憑證 |

適用於舊 stunnel／OpenSSL 組合無法協商對端要求的 TLS 的情境。執行檔已靜態連結 OpenSSL 及所需函式庫，不必另外安裝本專案的 `openssl` 指令。原始碼來自 [stunnel.org](https://www.stunnel.org/downloads.html)，舊版本下載失敗時會改查歷史封存路徑。

停用 TCP wrappers（libwrap）、systemd socket activation 與 FIPS 支援。這個 musl 靜態版本不能載入外部 OpenSSL provider 或 engine；可使用一般 PEM 憑證與私鑰。不匯出 `libstunnel.so` 或舊版 `stunnel3` wrapper。CA 憑證包、私鑰與設定檔都放在外部。

## Client 模式

預設設定路徑是 `/etc/stunnel/stunnel.conf`，也能直接傳入其他檔名。以下範例在本機 1143 埠接受明文連線，再建立經過驗證的 TLS 連線到 IMAP 伺服器：

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

請替換伺服器名稱與 CA 路徑。`verifyChain` 與 `checkHost` 應一起使用：只信任簽發者，並不等於驗證伺服器身分。明文 listener 只綁定 loopback。遠端服務與舊用戶端仍須使用相同應用協定；stunnel 不會轉換應用程式的登入驗證方式。

```bash
/opt/static/stunnel/stunnel -version
/opt/static/stunnel/stunnel /etc/stunnel/stunnel.conf
```

`foreground = yes`、`syslog = no` 與空白 `pid` 讓此範例不需要服務管理員或 root。若要在背景執行，請設定可寫入的 PID 路徑與日誌目的地。由 root 啟動的服務若使用 `setuid`、`setgid`，必須指定主機已存在的帳號。

## Server 模式

要透過 TLS 對外提供本機明文服務，可保留上述全域設定，將服務區塊改成：

```ini
[https]
client = no
accept = 0.0.0.0:8443
connect = 127.0.0.1:8080
cert = /path/to/fullchain.pem
key = /path/to/private-key.pem
sslVersionMin = TLSv1.2
```

請提供符合實際主機名稱的憑證，並限制私鑰檔案的存取權限。若需要雙向 TLS，另行設定用戶端憑證驗證。詳見[上游 HOWTO](https://www.stunnel.org/howto.html)。
