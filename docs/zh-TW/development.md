# 開發

[English](../development.md) · [新增一個程式](adding-a-target.md)

## 測試

```bash
python3 -B -m unittest discover -s tests -v
```

測試需要 Python 3。它模擬 Docker，不使用網路。涵蓋命令列用法、不改主程式就能新增目標、版本查詢失敗、取出執行檔失敗後的清理，以及拒絕動態連結的產物。

若目前目錄的 `./dist/<target>/` 已經有該目標的執行檔，同一組測試會再檢查它們。請在含有 `dist/` 的目錄執行。執行檔不存在就略過該目標。這些檢查不會啟動 Docker 編譯。

只有 `dist/<target>/VERSION` 存在時才比對版本，執行檔回報的版本必須與檔案相同。沒有這個檔案就略過版本比對。`build-static.sh` 會先寫入這個檔案，再執行對應的檢查。

| 目標 | 這組選擇性檢查涵蓋什麼 |
|------|------------------------|
| Apache | 靜態連結、event 與 prefork 的內建模組清單、這個目標的 APR 與 APR-util 版本、`htpasswd`，以及兩台伺服器各一次本機 HTTP 回應。HTTP 回應以 `nobody` 執行，需要 root。 |
| curl | 靜態連結，以及 `--version` 中的 HTTPS 與 HTTP/2。 |
| wget | 靜態連結，以及 `--version` 中的 HTTPS、zlib 與 PCRE2。 |
| rsync | 靜態連結、`--version`，以及一次本機檔案複製。 |
| OpenSSL | 靜態連結、`version`，以及一張自簽憑證。 |
| Git | 每個匯出的執行檔都是靜態連結。`--version`、絕對路徑的 `--exec-path`，以及一次本機 commit。 |
| OpenSSH | 該版本應有的每個執行檔都是靜態連結。`ssh -V` 決定 `sshd-session` 與 `sshd-auth` 是否必須存在。 |
| PHP | `php-cli`、`php-cgi` 與 `php-fpm` 都是靜態連結，並回報同一個 `x.y.z`。`php -m` 含這個目標選用的擴充功能。一次本機 FastCGI 回應用來檢查 `php-fpm`。以 root 執行時，worker 會切換到 `nobody`，所以需要這個帳號。 |
| nginx | 靜態連結、版本／建置選項、HTTP、代理、rewrite、驗證子請求、status、gzip／靜態 gzip、Brotli、TLS 1.2／1.3 與 HTTP/2 ALPN／SETTINGS。若有 `dist/php/php-fpm`，也執行 PHP-FPM 整合測試。HTTP/3 已編入但未實測握手。 |
| stunnel | 靜態連結／版本、TLS 1.2／1.3 server 轉送、經驗證的 TLS client 轉送，以及拒絕錯誤主機名稱或不受信任的憑證。 |

nginx 與 stunnel 的 TLS 測試需要 `openssl` 指令產生暫時憑證；找不到時會略過相關測試。服務檢查使用 loopback 暫時通訊埠、暫存設定檔與有逾時限制的程序清理，不需要連上網際網路。

新目標仍要實際用 Docker 編譯成功，才能把該版本列為已實測。

## 目錄

```text
musl-static-build/
├── build-static.sh          # 定位專案並載入 lib/build.sh
├── lib/
│   └── build.sh             # 參數、探索、驗證、Docker、匯出
├── targets/
│   ├── php/
│   ├── openssh/
│   ├── curl/
│   ├── wget/
│   ├── rsync/
│   ├── openssl/
│   ├── git/
│   ├── apache/
│   ├── nginx/
│   └── stunnel/             # 每個目錄有 target.sh 與 Dockerfile
├── tests/                   # unittest；執行期檢查是選擇性的
├── docs/                    # README 連出去的說明
├── README.md
├── README.zh-TW.md
└── dist/                    # 編譯輸出，已 gitignore，出現在你執行時的工作目錄
```

主程式載入指定模組，驗證並解析版本，再在該模組的 Dockerfile 後面加上靜態連結檢查與 `/out` 匯出。接著建置映像、複製宣告的執行檔，並移除暫時的容器。從容器複製失敗時也會移除容器。每個匯出的執行檔都會檢查，包含 PHP 的 CLI、CGI 與 FPM。

## 修改某個目標的建置

功能組合與編譯旗標寫在該目標的建置檔裡。命令列接受的是目標、版本、`--clean` 與 `--no-test`。`targets/<name>/target.sh` 負責版本、Alpine 版本與要匯出的檔名。

| 要改的內容 | 檔案 |
|------------|------|
| 多數目標的 `./configure`、`LDFLAGS` 與 `make` | `targets/<name>/Dockerfile` |
| Git 的 make 變數 | `targets/git/build.sh`。同一目錄的 Dockerfile 會另外編譯一份給 Git 用的小型靜態 libcurl |
| Apache 的 MPM、模組與 `CFLAGS` | `targets/apache/build-mpms.sh`。APR 與 APR-util 的旗標在 `targets/apache/Dockerfile` |

下一次編譯讀的是 `targets/<name>/Dockerfile`。主程式會把該檔重寫到 `dist/<target>/Dockerfile`，並附上靜態連結檢查。改 `dist/` 裡的那份，下次編譯會被蓋掉。

改到某個 `RUN`，或改到被 `COPY` 進映像的腳本（`targets/git/build.sh`、`targets/apache/build-mpms.sh`）時，Docker 會從該層起重編。要整段不用快取，加上 `--clean`。

已發布的測試，以及各目標頁的「已實測」，只涵蓋文件描述的預設建置。自行改過的執行檔仍須被判定為 `statically linked`，否則編譯會停止。改過的功能組合不在這個專案的支援範圍。Apache 與 nginx 保留 `-fno-pie` / `-no-pie`，這項檢查才過得了。這個 nginx 建置不使用 `-march=native`，成品才不會綁定編譯機的指令集。
