# `message_logger` — 系統日誌套件

## 架構概覽

```
SingletonSystemLogger（全域單例 orchestrator）
 ├── LoggerBase            格式化 + 全域 RUN_MODE 過濾 + adapter fan-out
 └── Adapters（可自由組合）
      ├── DarkThemeTerminalAdapter   (level_filter=DEBUG)   → 彩色 console（深色主題）
      ├── LightThemeTerminalAdapter  (level_filter=DEBUG)   → 彩色 console（淺色主題）
      ├── FileAdapter                (level_filter=WARNING) → thread-safe 本機日誌檔案
      ├── DarkThemeTkinterAdapter    (level_filter=INFO)    → Tkinter Text widget（深色主題）
      └── LightThemeTkinterAdapter   (level_filter=INFO)    → Tkinter Text widget（淺色主題）
```

**責任切分：**
- `LoggerBase` — 格式化訊息、全域 `RUN_MODE` 過濾、管理 adapter 清單、fan-out 廣播
- 各 `Adapter` — 持有自己的 `level_filter`，自行決定是否輸出，互相獨立

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

## 快速試用

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

---

## Adapter：`FileAdapter`（寫入本機檔案）

`FileAdapter` 使用獨立的 `threading.Lock`，可安全地在多執行緒環境中使用。

```python
from pathlib import Path
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, FileAdapter

logger = SingletonSystemLogger()
logger.clear_adapters()

# 基本用法：WARNING 以上才寫入檔案
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))

logger.info("這行不會進檔案")      # 被 WARNING filter 擋掉
logger.warning("這行會進檔案")
logger.error("這行也會進檔案")

# 驗證寫入內容
print(Path("app.log").read_text(encoding="utf-8"))
```

**進階選項：**

```python
# 覆寫模式（每次啟動清空檔案）
FileAdapter("DEBUG", Path("debug.log"), mode="w")

# 手動關閉（釋放檔案句柄）
adapter = FileAdapter("WARNING", Path("app.log"))
logger.register_adapter(adapter)
# ... 程式結束前 ...
adapter.close()
```

---

## Adapter：`TkinterAdapter`（Text widget 彩色輸出）

每個等級自動設定對應的 Tkinter Text **tag** 顏色；`shiny_log()` 額外套用粗體（`_SHINE` tag）。

```python
import tkinter as tk
from isd_py_framework_sdk.msg_logger import (
    SingletonSystemLogger,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
)

root = tk.Tk()
text = tk.Text(root)
text.pack(fill="both", expand=True)

logger = SingletonSystemLogger()
logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))

logger.info("INFO 訊息")
logger.warning("WARNING 訊息")
logger.shiny_log("閃亮節點", "CHECKPOINT")

root.mainloop()
```

**動態切換主題：**

```python
def set_theme(theme: str):
    logger.clear_adapters()
    if theme == "dark":
        text.configure(bg="#1e1e1e", fg="#ffffff")
        logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))
    else:
        text.configure(bg="#ffffff", fg="#000000")
        logger.register_adapter(LightThemeTkinterAdapter("INFO", tk_window=text))
```

**延遲注入 widget（先建 adapter，UI 初始化後再綁定）：**

```python
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTkinterAdapter

logger = SingletonSystemLogger()
adapter = DarkThemeTkinterAdapter("DEBUG")   # 先不傳 tk_window
logger.register_adapter(adapter)

# ... UI 建立完成後 ...
adapter.set_tk_window(text)                  # 注入 widget，同時套用所有 tag
```

**覆寫最後一行（適合進度更新）：**

```python
adapter = DarkThemeTkinterAdapter("INFO", tk_window=text)
logger.register_adapter(adapter)

logger.info("開始處理...")
# 進度更新時，直接覆寫最後一行而非新增一行
adapter.overwrite_last_line("INFO", "[2025-01-01 00:00:00] [INFO      ]: 處理中... 50%")
adapter.overwrite_last_line("INFO", "[2025-01-01 00:00:00] [INFO      ]: 處理中... 100%")
logger.success("完成！")
```

**Tag 顏色對應：**

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

---

## 組合多個 Adapter

```python
from pathlib import Path
from isd_py_framework_sdk.msg_logger import (
    SingletonSystemLogger,
    DarkThemeTerminalAdapter,
    FileAdapter,
    DarkThemeTkinterAdapter,
)

logger = SingletonSystemLogger()
logger.clear_adapters()

logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))          # console 顯示全部
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))    # 檔案只寫 WARNING+
# logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))  # UI 顯示 INFO+

logger.debug("只有 console 看得到")
logger.warning("console + 檔案都看得到")
```

---

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

---

## 全域開關與 Adapter 管理

```python
logger = SingletonSystemLogger()

# 暫時靜音（不影響 adapter 設定）
logger.disable_broadcast_msg()
logger.info("這行不會輸出")

logger.enable_broadcast_msg()
logger.info("重新輸出")

# 移除特定 adapter
logger.unregister_adapter(some_adapter)   # 若不存在，靜默忽略

# 清空全部
logger.clear_adapters()
```

---

## 環境變數控制（全域過濾）

全域 RUN_MODE 在程式啟動時讀取一次，執行期固定不變。
各 adapter 的 `level_filter` 是在此基礎上的第二層過濾。

| 變數 | 值 | 全域最低等級 | 說明 |
|---|---|---|---|
| `RUN_MODE` | `DEBUG`（預設） | DEBUG | 全部等級通過 |
| `RUN_MODE` | `DISPLAY` | INFO | DEBUG 被擋下 |
| `RUN_MODE` | `RUN` | ERROR | 僅 ERROR 以上通過（生產模式） |

```bash
# Linux / macOS
RUN_MODE=DISPLAY python your_script.py

# Windows PowerShell
$env:RUN_MODE="DISPLAY"; python your_script.py
```
