# 新增一個程式

[English](../adding-a-target.md) · [開發檢查](development.md)

新程式是 `targets/` 底下的一個目錄。主程式會自動找到它。命令列與 `lib/build.sh` 不用改。

```text
targets/<name>/target.sh     # 版本規則與產物檔名
targets/<name>/Dockerfile    # 下載、設定、靜態連結
```

`<name>` 以小寫字母開頭，其餘可以是小寫字母、數字、`_` 或 `-`。兩個檔案都放好之後，`./build-static.sh --list` 就會印出這個名稱。

curl 與 wget 是最適合照著抄的小型模組。

## target.sh

```bash
TARGET_DESCRIPTION="Example tool"
DEFAULT_VERSION="1.0.0"
VERSION_PATTERN='^[0-9]+\.[0-9]+\.[0-9]+$'
VERSION_HELP="x.y.z"
ALPINE_VERSION="3.20"
ARTIFACTS=("example:example")
```

| 變數 | 用途 |
|------|------|
| `TARGET_DESCRIPTION` | 說明與進度訊息裡顯示的名稱 |
| `DEFAULT_VERSION` | 指令省略版本時使用 |
| `VERSION_PATTERN` | 版本必須符合的 Bash 延伸正規表示式 |
| `VERSION_HELP` | 版本不符合時顯示的文字 |
| `ALPINE_VERSION` | 傳給建置參數 `ALPINE_VERSION` 的 Alpine 標籤 |
| `ARTIFACTS` | 每個要匯出的執行檔，格式是 `來源:輸出檔名` |

`來源` 相對於 Dockerfile 最後的 `WORKDIR`。`輸出檔名` 是寫入 `dist/<name>/` 的檔名。請列出所有要離開映像的執行檔。主程式會檢查對照、拒絕重複的輸出檔名，並拒絕 `file` 未描述為 `statically linked` 的執行檔。

`target.sh` 頂層只放賦值與函式定義。說明與目標探索會在子 Shell 載入這個檔案。網路請求和其他準備工作放在 `target_prepare()`。

### target_prepare

這個介面可有可無。它在版本驗證之後、寫出 Dockerfile 之前執行，可以改寫 `VERSION` 或 `ALPINE_VERSION`。PHP 用它把 `8.5` 變成當時最新的 `8.5.x`。OpenSSH 用它為 8.x 選擇 Alpine 3.16，並在沒有那些程式的版本拿掉 `sshd-session`／`sshd-auth`。

失敗時呼叫 `fail "訊息"`。它會印出 `Error: 訊息` 並結束。

這些模組是專案裡受信任的程式碼。主程式會直接載入並執行它們。

## Dockerfile

用來試介面的最小檔案：

```dockerfile
ARG ALPINE_VERSION=3.20
FROM alpine:${ALPINE_VERSION}
RUN apk add --no-cache build-base file
ARG VERSION
WORKDIR /usr/src/example-${VERSION}
RUN printf '#include <stdio.h>\nint main(void) { puts("example"); return 0; }\n' > example.c && \
    cc -static -Os -o example example.c && strip example
```

實際的程式請把範例編譯換成該程式的原始碼下載、設定與靜態連結。主程式會傳入建置參數 `VERSION` 與 `ALPINE_VERSION`。最終映像必須有 `file`、`grep`、`mkdir`、`cp`。主程式會在後面附加一段 `RUN`，檢查每個產物並複製到 `/out`。

Docker 的 build context 是 `targets/<name>/`。Dockerfile 裡 `COPY` 用到的檔案也放在這個目錄。

模組實際編譯成功之後，把實測版本寫進該程式的文件，以及 README 的表格。單元測試只模擬 Docker，不會編譯新程式。
