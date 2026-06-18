# `message_logger` — 系統日誌套件

## 安裝

```bash
# 終端機彩色輸出需要 colorama
pip install isd-py-framework-sdk[message_logger]
```

## 架構概覽

```
SingletonSystemLogger（全域單例 orchestrator）
 ├── LoggerBase            格式化 + 全域 RUN_MODE 過濾 + adapter fan-out
 └── Adapters（可自由組合）
      ├── DarkThemeTerminalAdapter   (level_filter=DEBUG)   → 彩色 console（深色主題）
      ├── LightThemeTerminalAdapter  (level_filter=DEBUG)   → 彩色 console（淺色主題）
      ├── FileAdapter                (level_filter=WARNING) → thread-safe 本機日誌檔案
      ├── DarkThemeTkinterAdapter    (level_filter=INFO)    → Tkinter Text widget（深色主題）
      ├── LightThemeTkinterAdapter   (level_filter=INFO)    → Tkinter Text widget（淺色主題）
      ├── DarkThemeTkLabelAdapter    (level_filter=INFO)    → tk.Label（深色主題）
      ├── LightThemeTkLabelAdapter   (level_filter=INFO)    → tk.Label（淺色主題）
      ├── DarkThemeTtkLabelAdapter   (level_filter=INFO)    → ttk.Label（深色主題）
      ├── LightThemeTtkLabelAdapter  (level_filter=INFO)    → ttk.Label（淺色主題）
      ├── LocalHTTPAdapter           (level_filter=INFO)    → JSON POST 到本機/遠端 endpoint（MVP）
      └── QueuedSocketAdapter        (level_filter=INFO)    → queue + worker 非阻塞 socket 傳送骨架
```

**責任切分：**
- `LoggerBase` — 格式化訊息、全域 `RUN_MODE` 過濾、管理 adapter 清單、fan-out 廣播
- 各 `Adapter` — 持有自己的 `level_filter`，自行決定是否輸出，互相獨立、互不知情

**推薦公開 API：**
- 一般使用者只需要 `SingletonSystemLogger`（或便捷函式 `get_logger()` / `configure_logger()`）加上 concrete adapters。
- 自訂輸出時才需要繼承 `LoggerAdapterBase`。
- `LoggerBase`、`Abstract*AdapterBase`、stub adapters 屬於進階或相容 API，不建議放在一般教學入口。

---

## Log Levels（由低到高）

| Level | 數值 | 用途 |
|---|---|---|
| `DEBUG` | 10 | 開發時詳細追蹤資訊 |
| `INFO` | 20 | 正常流程資訊 |
| `CHECKPOINT` | 22 | 關鍵流程節點 |
| `SUCCESS` | 25 | 操作成功 |
| `WARNING` | 30 | 潛在問題，不影響運行 |
| `ERROR` | 40 | 操作失敗，需修正 |
| `CRITICAL` | 50 | 致命錯誤，系統無法繼續 |
| `HIGHLIGHT` | 60 | 超醒目標記 |

---

## 快速試用（可直接貼到 terminal 執行）

```python
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTerminalAdapter

logger = SingletonSystemLogger()
logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))

logger.debug("除錯訊息")
logger.info("正常流程")
logger.checkpoint("關鍵節點")
logger.success("操作成功")
logger.warning("注意事項")
logger.error("發生錯誤")
logger.critical("致命錯誤")
logger.highlight("超醒目")
logger.shiny_log("閃亮登場", "SUCCESS")
```

也可以用便捷函式一次取得並設定 logger：

```python
from isd_py_framework_sdk.msg_logger import configure_logger, DarkThemeTerminalAdapter

# configure_logger 預設 clear=True（一次性啟動設定，會清空既有 adapter）
logger = configure_logger(DarkThemeTerminalAdapter(level_filter="DEBUG"))

# get_logger 預設 clear=False（singleton 疊加，不會清掉別處註冊的 adapter）
from isd_py_framework_sdk.msg_logger import get_logger
logger = get_logger(DarkThemeTerminalAdapter(level_filter="DEBUG"))
```

---

## Adapter：`TerminalAdapter`（彩色 console）

```python
from isd_py_framework_sdk.msg_logger import (
    SingletonSystemLogger,
    DarkThemeTerminalAdapter,
    LightThemeTerminalAdapter,
)

logger = SingletonSystemLogger()
logger.clear_adapters()

# 深色主題（適合黑色 / 深色終端）
logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))

# 或淺色主題（適合白色 / 淺色終端）
# logger.register_adapter(LightThemeTerminalAdapter("DEBUG"))

logger.info("INFO 訊息")
logger.warning("WARNING 訊息")

# 隨時調整單一 adapter 的過濾等級
adapter = DarkThemeTerminalAdapter("DEBUG")
adapter.set_filtered_level("WARNING")     # 現在只顯示 WARNING 以上
logger.register_adapter(adapter)
```

## Adapter：`FileAdapter`（寫入本機檔案）

`FileAdapter` 使用 `threading.Lock` 實作 thread-safe 寫入，可安全用於多執行緒場景。

```python
from pathlib import Path
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, FileAdapter

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))

logger.info("這行不會進檔案")          # 被 WARNING 過濾掉
logger.warning("這行會進檔案")
logger.error("這行也會進檔案")

print(Path("app.log").read_text(encoding="utf-8"))
```

**進階選項：**

```python
# 覆寫模式（每次啟動清空檔案）
FileAdapter("DEBUG", Path("debug.log"), mode="w")

# 關閉自動 flush（自行決定 flush 時機）
adapter = FileAdapter("INFO", Path("batch.log"), auto_flush=False)
logger.register_adapter(adapter)
# ... lots of logs ...
adapter.flush()
adapter.close()
```

## Adapter：`TkinterAdapter`（Text widget 彩色輸出）

每個等級自動設定對應的 Tkinter Text **tag** 顏色；`shiny_log()` 額外套用粗體（`_SHINE` tag）。

```python
import tkinter as tk
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTkinterAdapter

root = tk.Tk()
text = tk.Text(root)
text.pack(fill="both", expand=True)

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))

logger.info("INFO 訊息")
logger.warning("WARNING 訊息")
logger.shiny_log("閃亮節點", "CHECKPOINT")

root.mainloop()
```

**延遲注入 widget（先建 adapter，UI 初始化後再綁定）：**

```python
adapter = DarkThemeTkinterAdapter("DEBUG")   # 先不傳 tk_window
logger.register_adapter(adapter)

# ... UI 建立完成後 ...
adapter.set_tk_window(text)                 # 注入 widget，同時套用所有 tag
```

**覆寫最後一行（進度更新）**

```python
adapter = DarkThemeTkinterAdapter("INFO", tk_window=text)
logger.register_adapter(adapter)

logger.info("開始處理...")
adapter.overwrite_last_line("INFO", "[INFO] 處理中... 50%")
adapter.overwrite_last_line("INFO", "[INFO] 處理中... 100%")
logger.success("完成")
```

## Adapter：`TkLabelAdapter`（`tk.Label` 顯示最後一筆訊息）

```python
import tkinter as tk
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTkLabelAdapter

root = tk.Tk()
label = tk.Label(root, text="尚未有訊息")
label.pack(fill="x")

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(DarkThemeTkLabelAdapter("INFO", tk_label=label))

logger.info("系統初始化完成")
logger.warning("請注意設定值")

root.mainloop()
```

## Adapter：`TtkLabelAdapter`（`ttk.Label` 顯示最後一筆訊息）

```python
import tkinter as tk
from tkinter import ttk
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTtkLabelAdapter

root = tk.Tk()
label = ttk.Label(root, text="尚未有訊息")
label.pack(fill="x")

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(DarkThemeTtkLabelAdapter("INFO", ttk_label=label))

logger.success("資料載入成功")
logger.error("測試錯誤訊息")

root.mainloop()
```

**Tag 顏色對應（Tkinter / TkLabel / TtkLabel 系列共用）：**

| Level | Dark theme | Light theme |
|---|---|---|
| `DEBUG` | `#5599ff` | `#0000cc` |
| `INFO` | `#ffffff` | `#000000` |
| `CHECKPOINT` | `#66ffff` | `#007777` |
| `SUCCESS` | `#66ff66` | `#228B22` |
| `WARNING` | `#ffcc00` | `#aa007f` |
| `ERROR` | `#ff4444` | `#cc0000` |
| `CRITICAL` | `#ff44ff` | `#880088` |
| `HIGHLIGHT` | `#ffff33` | `#0055ff` |

> **注意：** Tkinter 只允許從主執行緒操作 widget。
> 若有跨執行緒 logging 需求，請在呼叫端使用 `widget.after()` 搭配 `queue.Queue`。

## 組合多個 Adapter

```python
from pathlib import Path
from isd_py_framework_sdk.msg_logger import (
    SingletonSystemLogger,
    DarkThemeTerminalAdapter,
    FileAdapter,
)

logger = SingletonSystemLogger()
logger.clear_adapters()

logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))         # console 顯示全部
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))   # 檔案只寫 WARNING+

logger.debug("只有 console 看得到")
logger.warning("console + 檔案都看得到")
```

## Adapter：`LocalHTTPAdapter`（MVP：JSON POST）

適合快速把 log 串到本機 listener（例如 FastAPI）做集中觀察。

```python
from isd_py_framework_sdk.msg_logger import (
    SingletonSystemLogger,
    LocalHTTPAdapter,
    DarkThemeTerminalAdapter,
)

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))
logger.register_adapter(
    LocalHTTPAdapter(
        "INFO",
        endpoint_url="http://127.0.0.1:8000/logs",
        timeout=0.5,
        fail_silently=True,
    )
)

logger.info("service boot")
logger.warning("high memory usage")
logger.error("network retry exhausted")
logger.flush_all()
```

## Adapter：`QueuedSocketAdapter`（骨架：queue + background worker）

`broadcast()` 路徑只負責 enqueue，避免主流程被 socket I/O 阻塞。

```python
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, QueuedSocketAdapter

logger = SingletonSystemLogger()
logger.clear_adapters()

socket_adapter = QueuedSocketAdapter(
    "INFO",
    host="127.0.0.1",
    port=9020,
    protocol="udp",  # or "tcp"
    max_queue_size=128,
    fail_silently=True,
)
logger.register_adapter(socket_adapter)

logger.info("socket-demo: service started")
logger.warning("socket-demo: queueing event")
logger.error("socket-demo: simulated error")

logger.flush_all()
socket_adapter.close()
```

## 自訂 Adapter

繼承 `LoggerAdapterBase` 並實作 `broadcast()` 即可接入 logger。

```python
from isd_py_framework_sdk.msg_logger import LoggerAdapterBase, SingletonSystemLogger

class SlackAdapter(LoggerAdapterBase):
    def __init__(self, level_filter: str, webhook_url: str):
        super().__init__(level_filter)
        self._url = webhook_url

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        # import requests
        # requests.post(self._url, json={"text": formatted})
        print(f"[Slack → {self._url}] {formatted}")

logger = SingletonSystemLogger()
logger.register_adapter(SlackAdapter("ERROR", "https://hooks.slack.com/..."))
logger.error("這則訊息會送到 Slack")
```

## 全域開關與 Adapter 管理

```python
logger = SingletonSystemLogger()

# 暫時靜音（不影響 adapter 設定）
logger.disable_broadcast_msg()
logger.info("這行不會輸出")

logger.enable_broadcast_msg()
logger.info("重新輸出")

# 移除特定 adapter
logger.unregister_adapter(some_adapter)

# 清空全部
logger.clear_adapters()
```

## 環境變數控制（全域過濾）

| 變數 | 值 | 說明 |
|---|---|---|
| `RUN_MODE` | `DEBUG`（預設） | 全部等級通過全域過濾 |
| `RUN_MODE` | `DISPLAY` | INFO 以上通過，DEBUG 被擋下 |
| `RUN_MODE` | `RUN` | 僅 ERROR 通過（生產模式） |

```bash
# Linux / macOS
RUN_MODE=DISPLAY python your_script.py
```

```powershell
# Windows PowerShell
$env:RUN_MODE="DISPLAY"; python your_script.py
```

> `RUN_MODE` 在 process 啟動時讀取一次，執行期間變更環境變數不會生效。

## 實作與測試範例索引（`tests/logger`）

直接執行下列腳本可看到各 adapter 的實際行為：

- `python tests/logger/test__msg_logger.py` — 全量 API 測試（Terminal / File / Tkinter / TkLabel / TtkLabel、stub adapters、thread-safe 寫入等）。
- `python tests/logger/combined_logger.py` — 綜合 GUI 範例：整合 `Text + tk.Label + ttk.Label + Terminal + File`，可切換主題。
- `python tests/logger/local_http_listener.py --host 127.0.0.1 --port 8000 --max-messages 3 --output-file tests/logger/http_listener.log` — 啟動本機 HTTP listener（FastAPI）。
- `python tests/logger/local_http_adapter_demo.py` — 搭配上述 listener 驗證 `LocalHTTPAdapter` 傳送。
- `python tests/logger/socket_listener.py --protocol udp --host 127.0.0.1 --port 9020 --max-messages 3 --output-file tests/logger/socket_listener.log` — 啟動本機 UDP listener（可改 `--protocol tcp`）。
- `python tests/logger/queued_socket_adapter_demo.py` — 驗證 `QueuedSocketAdapter` queue + worker 傳送路徑。

若使用 venv，建議改用虛擬環境 python：

```powershell
.venv\Scripts\python.exe tests/logger/test__msg_logger.py
```

---

開發/架構細節（adapter fan-out 設計規則、完整 adapter 一覽表）請見 [agent.md](agent.md)。
