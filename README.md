# ISD Python Framework

```
最底層的基礎架構套件，提供給所有 ISD 系列模組共用的底層設計模式與工具。
基於此套件開發的底層模組套件，將成為後續各專案的基石。
```

## 套件資訊

| 項目 | 值 |
|---|---|
| pip 安裝名 | `isd-python-framework` |
| Python import 名 | `hyper_framework` |
| 版本 | `0.0.1` |
| Python 需求 | `>= 3.11` |

---

## 安裝

### 一、從 `.whl` 安裝（使用者）
```bash
pip install isd_python_framework-*.whl
```

### 二、可編輯模式安裝（開發者）
```bash
pip install -e .
```

### 三、含 Excel 測試工具
```bash
pip install -e ".[excel]"
```

### 四、完整安裝（含所有 optional extras）
```bash
pip install -e ".[all]"
```

---

## 模組結構

```
hyper_framework/
├── base/               # 核心設計模式
├── events/             # 事件系統
├── message_logger/     # 系統日誌
├── decorators/         # 裝飾器工具
├── exceptions/         # 自訂例外
└── unitest_structure/  # 測試工具 (需 [excel] extras)
```

---

## `base` — 核心設計模式

### `SingletonMetaclass`

元類，讓任何類別自動實現執行緒安全的單例模式。
可選鉤子：若子類定義 `_initialize_manager(self)`，首次建立後自動呼叫一次。

```python
from hyper_framework import SingletonMetaclass

class MyManager(metaclass=SingletonMetaclass):
    def _initialize_manager(self):
        # 單例首次建立時執行一次
        self.data = []

a = MyManager()
b = MyManager()
print(a)
print(b)
assert a is b  # True
```

---

## `events` — 事件系統

### 事件基底類別：`IEventBase` / `IParsEventBase`

在你的專案中定義事件，繼承對應的基底類別：

```python
from hyper_framework import IEventBase, IParsEventBase
from dataclasses import dataclass

# 無參數事件
class OnDataReady(IEventBase): pass

# 帶參數事件
@dataclass
class OnDataLoaded(IParsEventBase):
    row_count: int
    source: str
```

---

### `SingletonEventManager`

全域單例事件匯流排，負責訂閱、取消訂閱、觸發事件。

支援兩種 callback 型別：
- **綁定方法**（bound methods）— 以 `WeakMethod` 保存，不延長物件生命週期
- **普通 callable**（module-level functions, static methods）— 以 `weakref.ref` 保存

> **注意：** lambda / local closure 沒有強引用持有者，訂閱後可能立即被 GC。
> 必須由呼叫端保持其強引用，或改用普通函式。

```python
from hyper_framework import SingletonEventManager, IEventBase, IParsEventBase
from dataclasses import dataclass

class OnJobDone(IEventBase): pass

@dataclass
class OnProgress(IParsEventBase):
    percent: float

em = SingletonEventManager()

# --- 綁定方法 callback ---
class Worker:
    def on_done(self):
        print("Job done!")

    def on_inner_progress(self, e: OnProgress):
        print(f"Inner Progress: {e.percent:.0%}")

    @staticmethod
    def on_progress(e: OnProgress):
        print(f"On Progress: {e.percent:.0%}")

    def subscribe(self):
        em.RegisterEvent(OnJobDone, self.on_done)
        em.RegisterEvent(OnProgress, self.on_progress)

    def unsubscribe(self):
        em.UnregisterEvent(OnJobDone, self.on_done)
        em.UnregisterEvent(OnProgress, self.on_progress)

# --- 普通函式 callback ---
def handle_done():
    print("Done (plain function)!")


print("=== OnJobDone ===")
em.RegisterEvent(OnJobDone, handle_done)
em.TriggerEvent(OnJobDone())
em.UnregisterEvent(OnJobDone, handle_done)

print("=== OnProgress ===")
em.RegisterEvent(OnProgress, Worker.on_progress)
em.TriggerEvent(OnProgress(percent=0.75))
em.UnregisterEvent(OnProgress, Worker.on_progress)

print("=== Worker Events ===")
w = Worker()
w.subscribe()
em.RegisterEvent(OnProgress, w.on_inner_progress)
em.TriggerEvent(OnJobDone())
em.TriggerEvent(OnProgress(percent=0.5))
```

```
=== OnJobDone ===
Done (plain function)!
=== OnProgress ===
On Progress: 75%
=== Worker Events ===
Job done!
On Progress: 50%
Inner Progress: 50%
```

**除錯模式：** 設定環境變數 `EVENT_MANAGER_DEBUGGER=1` 可印出詳細的事件類型解析資訊。

---

### `DelayEventBusManager`

延遲事件匯流排（Event Replay 模式）。

適用場景：訂閱者比發布者**晚初始化**，需要在訂閱後補齊(replay)先前已觸發過的事件。

```python
from hyper_framework import DelayEventBusManager, IDelayEventBase

class OnSystemReady(IDelayEventBase): pass

bus = DelayEventBusManager()

class LateModule:
    def _initialize(self):
        bus.RegisterEvent(OnSystemReady, self._on_system_ready)
        # 補齊之前已觸發過的事件
        bus.Evoke(OnSystemReady)

    def _on_system_ready(self):
        print("Caught up!")
```

> **One-shot 語意：** `Evoke` 執行後，對應事件的 callback 列表會被清空。

---

### `MulticastCallback`

通用的 callback 多播集合（Multicast），適合把多個處理器（例如：日誌、UI 更新、度量收集）綁在同一事件上。
支持直接呼叫、合併（回傳新物件）以及以單一 callback 為單位移除。

```python
from hyper_framework import MulticastCallback
from typing import Callable, List

# 實務範例：多個 handler 回應進度更新
on_progress: MulticastCallback[Callable[[int], None]] = MulticastCallback()

def log_progress(p: int):
    print(f"[LOG] progress={p}/100")

def update_ui(p: int):
    print(f"UI -> Progress bar set to {p}%")

metrics: List[int] = []
def collect_metric(p: int):
    metrics.append(p)
    print(f"[METRIC] collected {p/100:.2%}")

# 註冊 handlers
on_progress.add(collect_metric)  ## for data collecting
on_progress.add(log_progress)  ## for terminal debug
on_progress.add(update_ui)  ## for user interface

print("=== ALL ===")
# 廣播（所有已註冊的 handler 都會被呼叫）
on_progress(10)

print("\n=== AFTER REMOVAL ===")
# 移除某個 handler（- 回傳新 MulticastCallback；如要生效請重新指派或覆寫）
on_progress = on_progress - update_ui
on_progress(50)

print("\n=== COMBINED ===")
# 合併兩個 MulticastCallback（回傳新物件，不改變原本的 operands）
extra = MulticastCallback[Callable[[int], None]]()
extra.add(lambda p: print(f"extra handler: {p}"))
combined = on_progress + extra
combined(75)

print("\n=== RESULTS ===")
print("metrics:", metrics)
```

注意：`+` / `-` 運算子會回傳新物件；若要修改現有變數，請把結果重新指派回原變數（如範例所示）。

---

## `message_logger` — 系統日誌

### 架構概覽

```
SingletonSystemLogger（單例 orchestrator）
 ├── LoggerBase            格式化 + 全域 RUN_MODE 過濾 + adapter fan-out
 └── Adapters（可自由組合）
      ├── DarkThemeTerminalAdapter   (level_filter=DEBUG)   → 彩色 console（深色主題）
      ├── LightThemeTerminalAdapter  (level_filter=DEBUG)   → 彩色 console（淺色主題）
      ├── FileAdapter                (level_filter=WARNING) → 本機日誌檔案
      ├── DarkThemeTkinterAdapter    (level_filter=INFO)    → Tkinter Text widget（深色主題）
      └── LightThemeTkinterAdapter   (level_filter=INFO)    → Tkinter Text widget（淺色主題）
```

**責任切分：**
- `LoggerBase` — 格式化訊息、全域 `RUN_MODE` 過濾、管理 adapter 清單、fan-out 廣播
- 各 `Adapter` — 持有自己的 `level_filter`，自行決定是否輸出，互相獨立

---

### Log Levels（由低到高）

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

### 快速試用（可直接貼到 terminal 執行）

```python
from hyper_framework import SingletonSystemLogger, DarkThemeTerminalAdapter

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

### Adapter：`TerminalAdapter`（彩色 console）

```python
from hyper_framework import (
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

### Adapter：`FileAdapter`（寫入本機檔案）

```python
from pathlib import Path
from hyper_framework import SingletonSystemLogger, FileAdapter, DarkThemeTerminalAdapter

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))

logger.info("這行不會進檔案")          # 被 WARNING 過濾掉
logger.warning("這行會進檔案")
logger.error("這行也會進檔案")

# 驗證寫入內容
print(Path("app.log").read_text(encoding="utf-8"))
```

---

### Adapter：`TkinterAdapter`（Text widget 彩色輸出）

每個等級自動設定對應的 Tkinter Text **tag** 顏色；`shiny_log()` 額外套用粗體（`_SHINE` tag）。

```python
import argparse
import tkinter as tk
from hyper_framework.message_logger import (
    SingletonSystemLogger,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
)


def create_app(initial_theme: str = "dark"):
    root = tk.Tk()
    root.title("Logger Theme Switch")

    text = tk.Text(root)
    text.pack(fill="both", expand=True)

    logger = SingletonSystemLogger()

    def set_theme(theme: str):
        logger.clear_adapters()
        if theme == "dark":
            text.configure(bg="#1e1e1e", fg="#ffffff")
            logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))
        else:
            text.configure(bg="#ffffff", fg="#000000")
            logger.register_adapter(LightThemeTkinterAdapter("INFO", tk_window=text))

    def toggle_theme():
        root.current_theme = "light" if root.current_theme == "dark" else "dark"
        set_theme(root.current_theme)

    btn = tk.Button(root, text="Toggle Theme", command=toggle_theme)
    btn.pack(anchor="ne", padx=8, pady=8)

    root.current_theme = initial_theme
    set_theme(root.current_theme)

    # Example logs to show in the text widget
    logger.info("INFO 訊息")
    logger.warning("WARNING 訊息")
    logger.shiny_log("閃亮節點", "CHECKPOINT")

    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tkinter logger theme switcher")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="initial theme")
    args = parser.parse_args()

    app = create_app(initial_theme=args.theme)
    app.mainloop()
```

**延遲注入 widget（先建 adapter，UI 初始化後再綁定）：**

```python
from hyper_framework.message_logger import SingletonSystemLogger, DarkThemeTkinterAdapter

logger = SingletonSystemLogger()
adapter = DarkThemeTkinterAdapter("DEBUG")   # 先不傳 tk_window
logger.register_adapter(adapter)

# ... UI 建立完成後 ...
# adapter.set_tk_window(text)               # 注入 widget，同時套用所有 tag
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

### 組合多個 Adapter

```python
from pathlib import Path
from hyper_framework.message_logger import (
    SingletonSystemLogger,
    DarkThemeTerminalAdapter,
    FileAdapter,
    DarkThemeTkinterAdapter,
)

logger = SingletonSystemLogger()
logger.clear_adapters()

logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))         # console 顯示全部
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))   # 檔案只寫 WARNING+
# logger.register_adapter(DarkThemeTkinterAdapter("INFO", tk_window=text))  # UI 顯示 INFO+

logger.debug("只有 console 看得到")
logger.warning("console + 檔案都看得到")
```

---

### 自訂 Adapter

繼承 `LoggerAdapterBase` 並實作 `broadcast()` 即可接入 logger。

```python
from hyper_framework.message_logger import LoggerAdapterBase, SingletonSystemLogger

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

### 全域開關與 Adapter 管理

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

---

### 環境變數控制（全域過濾）

| 變數 | 值 | 說明 |
|---|---|---|
| `RUN_MODE` | `DEBUG`（預設） | 全部等級通過全域過濾 |
| `RUN_MODE` | `DISPLAY` | INFO 以上通過，DEBUG 被擋下 |
| `RUN_MODE` | `RUN` | 僅 ERROR 通過（生產模式） |

```bash
# Linux / macOS
RUN_MODE=DISPLAY python your_script.py

# Windows PowerShell
$env:RUN_MODE="DISPLAY"; python your_script.py
```



## `decorators` — 裝飾器工具

```python
from hyper_framework import function_timer, timed_and_conditional_return, deprecated, battered

@function_timer
def slow_task():
    ...  # 自動印出執行時間

@timed_and_conditional_return
def measured_task():
    return "result"

result = measured_task()                        # 回傳 "result"
result, elapsed = measured_task(with_time_return=True)  # 回傳 ("result", 秒數)

@deprecated("Use `new_func` instead.")
def old_func(): ...

@battered("Fragile with edge cases.")
def risky_func(): ...
```

---

## `exceptions` — 自訂例外

```python
from hyper_framework import (
    WrongOptionException,
    WrongImplementationException,
    UnhandledConditionError,
    RepeatedInitializationError,
)

# 無效選項
raise WrongOptionException(option="mode_x")

# 錯誤使用方式
raise WrongImplementationException(restriction="此方法不可在 __init__ 中呼叫")

# if-elif 未覆蓋的狀態
raise UnhandledConditionError(state=current_state, value=val)

# 物件被重複初始化
raise RepeatedInitializationError()
```

---

## `unitest_structure` — 測試工具（需 `[excel]` extras）

### 型別斷言

```python
from hyper_framework.unitest_structure import (
    assert__is_str,
    assert__is_list_of_str,
    assert__is_list_of_list_of_str,
    assert__is_list_of_tuple_of_str,
)

assert__is_str("hello")                        # OK
assert__is_list_of_str(["a", "b"])             # OK
assert__is_list_of_list_of_str([["a"], ["b"]]) # OK
```

### Excel 結構核對

```python
from hyper_framework.unitest_structure.excel_unittest_module import compare_excel_sheets

compare_excel_sheets({
    "target_path": "output.xlsx",
    "bench_path":  "expected.xlsx",
    "sheets": [
        {
            "target_sheet": "Result",
            "bench_sheet":  "Result",
            "checks": [],
        }
    ],
})
```

---

## 版本查詢（CLI）

```bash
isd-python-framework -V
isd-python-framework --version
```

---

## 建置 `.whl`

```powershell
.\builder__whl.ps1
```
或
```bat
builder__whl.bat
```

---

## Acknowledgements / 銘謝

本專案的底層架構原先在國立台灣大學（NTU）實驗室擔任工程師期間開發，
從個人專案 `ACA`（完全由本人開發，約 60k+ 行）中抽取整理而來。
詳見 `AUTHORS.md`。


