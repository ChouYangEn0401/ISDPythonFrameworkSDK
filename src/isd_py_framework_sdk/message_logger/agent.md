# agent.md — `message_logger` 套件

## 職責

提供結構化、可組合的 logging 系統。核心概念是 **Adapter fan-out**：一個 singleton orchestrator（`SingletonSystemLogger`）接收 log 呼叫，然後廣播給所有已註冊的 adapter；每個 adapter 各自決定是否輸出（依自己的 `level_filter`）。

---

## 架構

```
message_logger/
├── __init__.py                       公開 API（含 get_logger / configure_logger helpers）
├── SingletonSystemLogger.py          主要單例（繼承 LoggerBase + SingletonMetaclass）
├── SingletonSystemLogger.pyi         型別存根
├── adapters.py                       所有內建 Adapter 實作
├── base/
│   ├── levels.py                     Log level 定義（LogLevelLiteral, LevelOrder）
│   ├── LoggerAdapterBase.py          Adapter 抽象基底（擴充點）
│   ├── LoggerBase.py                 格式化 + 全域過濾 + fan-out 核心邏輯
│   └── __init__.py
├── README.md                         完整使用文件
└── MY_OLD_DEV_NOTION.md              舊版開發筆記（歷史參考）
```

---

## 層次結構

```
SingletonSystemLogger  (singleton orchestrator)
    └── LoggerBase     (格式化 + RUN_MODE 過濾 + adapter 管理 + fan-out)
         └── 各 Adapter (持有獨立 level_filter，實作 broadcast())
              ├── DarkThemeTerminalAdapter / LightThemeTerminalAdapter
              ├── FileAdapter
              ├── DarkThemeTkinterAdapter / LightThemeTkinterAdapter
              ├── DarkThemeTkLabelAdapter / LightThemeTkLabelAdapter
              ├── DarkThemeTtkLabelAdapter / LightThemeTtkLabelAdapter
              ├── LocalHTTPAdapter
              └── QueuedSocketAdapter
```

---

## Log Levels（數值低→高）

| Level | 數值 | 用途 |
|---|---|---|
| `DEBUG` | 10 | 開發追蹤 |
| `INFO` | 20 | 正常流程 |
| `CHECKPOINT` | 22 | 關鍵流程節點 |
| `SUCCESS` | 25 | 操作成功 |
| `WARNING` | 30 | 潛在問題 |
| `ERROR` | 40 | 操作失敗 |
| `CRITICAL` | 50 | 致命錯誤 |
| `HIGHLIGHT` | 60 | 超醒目標記 |

自訂 level 字串在 `base/levels.py` 的 `LevelOrder` dict 中定義，排序與過濾邏輯依賴此 dict。

---

## 全域 RUN_MODE 過濾

`LoggerBase` 在模組載入時讀取 `RUN_MODE` 環境變數一次（**執行期固定，不可動態改變**）：

| `RUN_MODE` 值 | 等效最低 level |
|---|---|
| `DEBUG`（預設）| `DEBUG` |
| `DISPLAY` | `INFO` |
| `RUN` | `ERROR` |

---

## 核心 API

```python
from isd_py_framework_sdk.message_logger import (
    SingletonSystemLogger, get_logger, configure_logger,
    DarkThemeTerminalAdapter, FileAdapter, LoggerAdapterBase,
)

# 方式一：singleton 直接操作
logger = SingletonSystemLogger()
logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))
logger.info("訊息")
logger.shiny_log("閃亮", "CHECKPOINT")  # 帶粗體

# 方式二：helper 函式（推薦用於應用程式啟動路徑）
logger = configure_logger(DarkThemeTerminalAdapter("DEBUG"), FileAdapter("WARNING", Path("app.log")))

# 方式三：非破壞性取得 + 附加 adapter
logger = get_logger(DarkThemeTerminalAdapter("DEBUG"))  # 不清除現有 adapters
```

`configure_logger` 預設 `clear=True`（清空現有 adapters）；`get_logger` 預設 `clear=False`（附加）。

---

## Adapter 設計規則

實作自訂 adapter 只需繼承 `LoggerAdapterBase` 並實作 `broadcast()`：

```python
class MyAdapter(LoggerAdapterBase):
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.normalize_level(level)        # 標準化大寫
        if not self.should_emit(level):            # 套用 level_filter
            return
        # 你的輸出邏輯
```

`level_filter` 建構子第一個參數，傳入字串 level 名稱（如 `"DEBUG"`, `"WARNING"`）。`should_emit()` 是 base class 提供的過濾方法。

---

## Adapter 種類摘要

| Adapter | 輸出目標 | 特殊能力 |
|---|---|---|
| `DarkThemeTerminalAdapter` | console（深色主題）| colorama 彩色 |
| `LightThemeTerminalAdapter` | console（淺色主題）| colorama 彩色 |
| `FileAdapter` | 本機檔案 | `threading.Lock` thread-safe；`mode="w"` 覆寫；`auto_flush` 控制 |
| `DarkThemeTkinterAdapter` | `tk.Text` widget | tag 彩色；`overwrite_last_line()` 進度覆寫；延遲 `set_tk_window()` |
| `LightThemeTkinterAdapter` | `tk.Text` widget | 同上（淺色） |
| `DarkThemeTkLabelAdapter` | `tk.Label` | 只顯示最後一筆 |
| `LightThemeTkLabelAdapter` | `tk.Label` | 同上（淺色） |
| `DarkThemeTtkLabelAdapter` | `ttk.Label` | 只顯示最後一筆 |
| `LightThemeTtkLabelAdapter` | `ttk.Label` | 同上（淺色） |
| `LocalHTTPAdapter` | HTTP JSON POST | `fail_silently`；MVP 等級 |
| `QueuedSocketAdapter` | TCP/UDP socket | queue + background worker；非阻塞 |
| `HTMLAdapter` / `HTTPAdapter` / `DBAdapter` / `WebsocketAdapter` | （骨架/預留）| 尚未完整實作 |

---

## Adapter 管理 API

```python
logger.register_adapter(adapter)    # add_adapter() 等同，後者同時回傳 adapter
logger.unregister_adapter(adapter)  # remove_adapter() 是 alias
logger.clear_adapters()
logger.disable_broadcast_msg()      # 靜音（不影響 adapter 設定）
logger.enable_broadcast_msg()
logger.flush_all()                  # 所有 adapter 強制 flush
```

---

## 進入點與 Import

```python
# 推薦：子套件路徑
from isd_py_framework_sdk.message_logger import SingletonSystemLogger, DarkThemeTerminalAdapter
# 短路徑別名（向下相容）
from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTerminalAdapter
```

---

## 測試與範例

```powershell
.venv\Scripts\python.exe tests/logger/test__msg_logger.py         # 全量 API 測試
.venv\Scripts\python.exe tests/logger/combined_logger.py          # 綜合 GUI 範例
.venv\Scripts\python.exe tests/logger/terminal_logger.py
.venv\Scripts\python.exe tests/logger/file_logger.py

# LocalHTTPAdapter 測試（需兩個終端）
.venv\Scripts\python.exe tests/logger/local_http_listener.py --host 127.0.0.1 --port 8000 --max-messages 3 --output-file tests/logger/http_listener.log
.venv\Scripts\python.exe tests/logger/local_http_adapter_demo.py

# QueuedSocketAdapter 測試
.venv\Scripts\python.exe tests/logger/socket_listener.py --protocol udp --host 127.0.0.1 --port 9020
.venv\Scripts\python.exe tests/logger/queued_socket_adapter_demo.py
```

---

## 常見陷阱

- `colorama` 是 optional dependency（`[message_logger]` extras）；`adapters.py` 頂層直接 `from colorama import ...`，如未安裝會在 import 時 `ImportError`。
- Tkinter adapter 只能從主執行緒呼叫 widget 方法（Tkinter 的限制），跨執行緒需用 `widget.after()` + `queue.Queue` 中轉。
- `RUN_MODE` 環境變數在模組載入時讀取一次；無法在 runtime 動態改變全域過濾。
- `SingletonSystemLogger` 是單例；`clear_adapters()` 清空後，同一進程其他地方若保有對 logger 的引用，log 就會無聲無息地消失。
