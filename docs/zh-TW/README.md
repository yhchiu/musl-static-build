# 文件

[English](../README.md)

這裡放首頁放不下的說明。使用方式從「在舊主機執行」開始即可。

| 文件 | 適合什麼時候讀 |
|------|----------------|
| [編譯與檢查](usage.md) | 選擇版本、使用 `--clean` 或 `--no-test`、確認檔案寫到哪裡 |
| [在舊主機執行](running-on-old-hosts.md) | 把編譯好的檔案複製到無法升級 glibc 的機器 |
| [PHP](targets/php.md) | CLI、CGI、PHP-FPM、擴充功能、版本查詢 |
| [OpenSSH](targets/openssh.md) | 安裝 `sshd` 與 `/usr/libexec` 裡的輔助程式 |
| [curl](targets/curl.md) | 使用 HTTPS、HTTP/2，以及指定 CA 憑證 |
| [wget](targets/wget.md) | 使用 HTTPS，以及指定 CA 憑證 |
| [rsync](targets/rsync.md) | 用 zstd、lz4 與 xxHash 複製檔案 |
| [OpenSSL](targets/openssl.md) | 使用 `openssl` 指令，以及指定 CA 憑證 |
| [Git](targets/git.md) | 從同一個目錄使用 `git` 與 HTTPS 輔助程式 |
| [Apache httpd](targets/apache.md) | 撰寫已內建模組的設定檔 |
| [nginx](targets/nginx.md) | 使用內建網站／stream 模組、Brotli、TLS 與 PHP-FPM |
| [stunnel](targets/stunnel.md) | 設定 TLS client／server 轉送與憑證驗證 |
| [新增一個程式](adding-a-target.md) | 只新增 `targets/<name>/`，不改共用流程 |
| [開發](development.md) | 執行測試、看目錄結構、修改某個目標的建置 |
