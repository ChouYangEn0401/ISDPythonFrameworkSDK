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
├── base/                      # 核心設計模式
├── events/                    # 事件系統
├── message_logger/            # 系統日誌
├── helpers/                   # 工具集
│   ├── assertions/
│   │   ├── type_assertions.py         # 型別斷言（str / int / list / dict…）
│   │   ├── value_assertions.py        # 值域斷言（正數 / 範圍 / 成員 / regex）
│   │   └── collection_assertions.py   # 集合斷言（長度 / 唯一性 / keys / contains）
│   ├── decorators/
│   │   ├── profiling.py               # 計時、呼叫計數、記憶體 profiling
│   │   ├── lifecycle.py               # API 版本標記（deprecated / experimental…）
│   │   ├── control_flow.py            # 流程控制（retry / once / throttle / timeout）
│   │   ├── concurrency.py             # 併發工具（run_in_thread / synchronized）
│   │   ├── etl.py                     # ETL 管線步驟標記與日誌
│   │   ├── validation.py              # 輸入 / 輸出邊界防衛
│   │   ├── gui.py                     # GUI 執行緒安全、防抖、元件助手
│   │   ├── monitoring.py              # 指標、watchdog、健康檢查、速率限制
│   │   ├── ai_training.py             # ML 訓練 / 推論生命週期防衛
│   │   └── architecture.py            # SRP / 層次邊界 / 介面合約執行
│   └── exceptions/
│       ├── lifecycle.py               # 生命週期例外
│       ├── options.py                 # 選項 / 設定管理例外
│       ├── architecture.py            # 架構設計違反例外
│       ├── flow_control.py            # 流程控制例外
│       ├── validation.py              # 驗證例外
│       ├── runtime.py                 # 運行時一般例外
│       ├── etl.py                     # ETL 管線例外
│       ├── gui.py                     # GUI 操作例外
│       ├── monitoring.py              # 監察 / 觀測例外
│       └── ai_training.py             # AI / ML 訓練例外
└── unitest_structure/         # 測試工具 (需 [excel] extras)
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



## `helpers.assertions` — 斷言工具

所有斷言成功回傳 `True`，失敗拋出 `TypeError` / `ValueError` / `KeyError`。
可直接從頂層匯入，也可從子模組精準匯入。

```python
from hyper_framework import (
    # 型別斷言
    assert__is_str, assert__is_int, assert__is_float, assert__is_number,
    assert__is_bool, assert__is_dict, assert__is_list, assert__is_tuple,
    assert__is_set, assert__is_callable, assert__is_none, assert__is_not_none,
    assert__is_instance, assert__is_subclass,
    # 複合型別斷言
    assert__is_list_of_str, assert__is_list_of_int, assert__is_list_of_float,
    assert__is_list_of_number, assert__is_list_of_list_of_str,
    assert__is_list_of_tuple_of_str, assert__is_dict_of_str_to_str,
    # 值域斷言
    assert__is_positive, assert__is_non_negative, assert__is_not_empty,
    assert__in_range, assert__is_one_of, assert__matches_pattern,
    # 集合斷言
    assert__has_length, assert__min_length, assert__max_length,
    assert__all_keys_exist, assert__is_unique, assert__no_none_values,
)
```

### 型別斷言 (`type_assertions`)

| 函式 | 說明 |
|---|---|
| `assert__is_str(obj)` | 必須是 `str` |
| `assert__is_int(obj)` | 必須是 `int`（`bool` 排除） |
| `assert__is_float(obj)` | 必須是 `float` |
| `assert__is_number(obj)` | 必須是 `int \| float`（`bool` 排除） |
| `assert__is_bool(obj)` | 必須是 `bool` |
| `assert__is_dict(obj)` | 必須是 `dict` |
| `assert__is_list(obj)` | 必須是 `list` |
| `assert__is_tuple(obj)` | 必須是 `tuple` |
| `assert__is_set(obj)` | 必須是 `set` |
| `assert__is_callable(obj)` | 必須是 callable |
| `assert__is_none(obj)` | 必須是 `None` |
| `assert__is_not_none(obj)` | 不得為 `None` |
| `assert__is_instance(obj, cls)` | `isinstance` 檢查 |
| `assert__is_subclass(cls, parent)` | `issubclass` 檢查 |
| `assert__is_list_of_str(obj)` | `list[str]` |
| `assert__is_list_of_int(obj)` | `list[int]` |
| `assert__is_list_of_float(obj)` | `list[float]` |
| `assert__is_list_of_number(obj)` | `list[int \| float]` |
| `assert__is_list_of_list_of_str(obj)` | `list[list[str]]` |
| `assert__is_list_of_tuple_of_str(obj)` | `list[tuple[str, ...]]` |
| `assert__is_dict_of_str_to_str(obj)` | `dict[str, str]` |

### 值域斷言 (`value_assertions`)

| 函式 | 說明 |
|---|---|
| `assert__is_positive(obj)` | 必須 > 0 |
| `assert__is_non_negative(obj)` | 必須 >= 0 |
| `assert__is_not_empty(obj)` | 不得為 `None` 或空容器/字串 |
| `assert__in_range(obj, low, high, *, inclusive=True)` | 值域範圍檢查 |
| `assert__is_one_of(obj, options)` | 成員資格檢查 |
| `assert__matches_pattern(obj, pattern)` | 正規表達式全匹配 |

### 集合斷言 (`collection_assertions`)

| 函式 | 說明 |
|---|---|
| `assert__has_length(obj, n)` | `len(obj) == n` |
| `assert__min_length(obj, n)` | `len(obj) >= n` |
| `assert__max_length(obj, n)` | `len(obj) <= n` |
| `assert__all_keys_exist(d, keys)` | dict 必須包含所有指定 keys |
| `assert__is_unique(obj)` | 元素不得重複 |
| `assert__no_none_values(obj)` | 不得含有 `None` 值 |

```python
# 使用範例
assert__is_int(42)                          # OK
assert__is_number(3.14)                      # OK
assert__is_not_empty(["a", "b"])             # OK
assert__in_range(5, 1, 10)                   # OK
assert__is_one_of("dark", ["dark", "light"]) # OK
assert__all_keys_exist({"a": 1, "b": 2}, ["a", "b"])  # OK
assert__matches_pattern("abc-123", r"[a-z]+-\d+")     # OK
```

---

## `helpers.decorators` — 裝飾器工具

所有裝飾器可直接從頂層匯入：

```python
from hyper_framework import function_timer, retry, etl_step, ...
```

也可精準匯入（適合減少 import 污染）：

```python
from hyper_framework.helpers.decorators.profiling import log_call
```

---

### Profiling — 計時 / 呼叫計數 / 記憶體

| 裝飾器 | 說明 |
|---|---|
| `@function_timer` | 印出函式執行時間（wall-clock）|
| `@timed_and_conditional_return` | 計時；傳入 `with_time_return=True` 回傳 `(result, elapsed)` |
| `@log_call(show_args, show_return)` | 在每次呼叫前後印出函式名稱、參數、回傳值 |
| `@count_calls` | 累計呼叫次數，結果存在 `func.call_count` |
| `@profile_memory` | 以 `tracemalloc` 測量記憶體峰值，印出每次呼叫的△ KB |

```python
from hyper_framework import function_timer, timed_and_conditional_return, log_call, count_calls, profile_memory

@function_timer
def slow_task():
    import time; time.sleep(0.1)

@timed_and_conditional_return
def measured():
    return 42

result = measured()                         # → 42
result, elapsed = measured(with_time_return=True)  # → (42, 0.000…)

@log_call(show_args=True, show_return=True)
def add(a, b):
    return a + b

@count_calls
def ping(): ...
ping(); ping()
print(ping.call_count)  # 2

@profile_memory
def load_big_file(path): ...
```

---

### Lifecycle — API 版本標記

| 裝飾器 | 說明 |
|---|---|
| `@deprecated(reason)` | 每次呼叫發出 `DeprecationWarning` |
| `@battered(reason)` | 每次呼叫發出 `UserWarning`（強調易崩潰）|
| `@experimental(reason)` | **第一次**呼叫發出 `FutureWarning`（API 不穩定）|
| `@removed_in(version, reason)` | 每次呼叫提示將在 *version* 版本移除 |
| `@since(version)` | 靜態標記，說明此 API 自 *version* 起引入，無運行期副作用 |

```python
from hyper_framework import deprecated, battered, experimental, removed_in, since

@deprecated("Use `new_func` instead.")
def old_func(): ...

@battered("Fails with empty inputs.")
def risky_func(): ...

@experimental("Behaviour may change in v2.")
def new_feature(): ...

@removed_in("2.0.0", reason="Use `new_api()` instead.")
def legacy_api(): ...

@since("1.3.0")
def stable_feature(): ...
```

---

### Control Flow — 流程控制

| 裝飾器 | 說明 |
|---|---|
| `@retry(max_attempts, delay, backoff, exceptions)` | 自動重試，支援延遲與指數退避 |
| `@once` | 只執行一次，後續呼叫直接回傳快取結果 |
| `@suppress_exceptions(*exc, default, log)` | 攔截指定例外，回傳 `default` 值 |
| `@throttle(interval)` | 節流：同一函式每 *interval* 秒最多觸發一次 |
| `@timeout(seconds)` | 超過指定秒數拋 `TimeoutError` |

```python
from hyper_framework import retry, once, suppress_exceptions, throttle, timeout

@retry(max_attempts=5, delay=1.0, backoff=2.0, exceptions=(IOError,))
def fetch(): ...  # 最多重試 5 次，延遲 1→2→4→8 秒

@once
def load_config():
    return {"key": "value"}
# 第一次呼叫執行；後續呼叫直接回傳快取

@suppress_exceptions(ZeroDivisionError, default=-1, log=True)
def safe_div(a, b): return a / b
# safe_div(1, 0) → -1

@throttle(2.0)
def heartbeat(): ...  # 2 秒內只執行一次

@timeout(5.0)
def slow_call(): ...  # 超過 5 秒拋 TimeoutError
```

---

### Concurrency — 併發工具

| 裝飾器 | 說明 |
|---|---|
| `@run_in_thread` | 在 daemon thread 中執行，立即回傳 `Thread` 物件 |
| `@synchronized` / `@synchronized(lock)` | 以 `Lock` 串列化存取，可多函式共用同一把鎖 |

```python
from hyper_framework import run_in_thread, synchronized
import threading

@run_in_thread
def bg_task():
    import time; time.sleep(2)

t = bg_task()   # 非阻塞，立即回傳
t.join()

shared_lock = threading.Lock()

@synchronized(shared_lock)
def write_a(): ...

@synchronized(shared_lock)
def write_b(): ...  # write_a 與 write_b 互斥
```

---

### ETL — 管線步驟標記

| 裝飾器 | 說明 |
|---|---|
| `@etl_step(name, stage)` | 印出步驟標頭/結尾及耗時；`stage` 可為 `"extract"/"transform"/"load"` |
| `@log_record_count(label)` | 函式返回後印出 `len(result)` |
| `@checkpoint(save_fn)` | 成功後呼叫 `save_fn(result)` 持久化；失敗只警告不中斷 |
| `@skip_on_empty` | 若第一個引數為空容器（`len == 0`）則直接回傳 `None` |
| `@idempotent_load` | 以引數 hash 快取結果；相同引數不重複執行 |

```python
from hyper_framework import etl_step, log_record_count, checkpoint, skip_on_empty, idempotent_load

@etl_step(name="Load Users", stage="extract")
def load_users(path): return open(path).readlines()

@log_record_count("rows")
def transform(rows): return [r.strip() for r in rows]

def save_parquet(df): df.to_parquet("ckpt.parquet")

@checkpoint(save_parquet)
def heavy_transform(df): ...

@skip_on_empty
def process(records): ...   # records 為空時直接回傳 None

@idempotent_load
def fetch_api(endpoint): ...  # 相同 endpoint 只呼叫一次
```

---

### Validation — 輸入 / 輸出防衛

| 裝飾器 | 說明 |
|---|---|
| `@not_none(*arg_names)` | 指定參數不得為 `None` |
| `@validate_args(**validators)` | 每個參數對應一個 `predicate`，失敗拋 `ValueError` |
| `@validate_return(validator, message)` | 驗證回傳值，失敗拋 `ValueError` |
| `@ensure_type(**type_map)` | 指定參數必須為指定型別 |
| `@clamp_return(low, high)` | 將數值回傳值強制限制在 `[low, high]` |
| `@non_empty_return` | 回傳值不得為空容器或 `None` |

```python
from hyper_framework import not_none, validate_args, validate_return, ensure_type, clamp_return, non_empty_return

@not_none("user_id", "payload")
def create_record(user_id, payload): ...

@validate_args(
    age=lambda v: isinstance(v, int) and v >= 0,
    name=lambda v: isinstance(v, str) and len(v) > 0,
)
def register(name, age): ...

@validate_return(lambda v: len(v) > 0, message="must be non-empty list")
def fetch_items(): return []

@ensure_type(path=str, count=int)
def read_file(path, count): ...

@clamp_return(0, 100)
def score(): return 150   # 回傳 100

@non_empty_return
def get_names(): return []  # 拋 ValueError
```

---

### GUI — 執行緒安全 / 防抖 / 元件助手

| 裝飾器 | 說明 |
|---|---|
| `@require_main_thread` | 非主執行緒呼叫時拋 `RuntimeError`（保護 Tkinter / Qt widget）|
| `@debounce(wait)` | 防抖：靜止 *wait* 秒後才執行，中途呼叫重置計時器 |
| `@gui_error_handler(on_error)` | 攔截 GUI handler 中的例外，呼叫 `on_error(exc)` 而非崩潰 |
| `@disable_widget_during_run(widget)` | 函式執行期間自動 disable / re-enable widget |
| `@run_after(delay_ms, scheduler)` | 延遲 *delay_ms* 毫秒後在主執行緒執行（預設用 `widget.after`）|

```python
from hyper_framework import require_main_thread, debounce, gui_error_handler

@require_main_thread
def update_label(text):
    label.config(text=text)  # 背景執行緒呼叫此函式會立即拋錯

@debounce(0.3)
def on_search(text):
    ...  # 使用者停止輸入 0.3 秒後才觸發

@gui_error_handler(on_error=lambda e: status_bar.set(str(e)))
def on_button_click():
    risky_operation()  # 例外不會崩潰 GUI
```

---

### Monitoring — 指標 / Watchdog / 健康檢查

| 裝飾器 | 說明 |
|---|---|
| `@emit_metric(name, unit)` | 呼叫完成後印出（或傳送）wall-clock 耗時指標 |
| `@watchdog_ping(registry, key)` | 每次呼叫更新 `registry[key]` 為當前時間戳（確認存活）|
| `@health_check(on_failure)` | 成功回傳 `True`、失敗回傳 `False`（不重拋，適合探針）|
| `@alert_on_failure(on_alert)` | 例外時呼叫 `on_alert(exc)` 再重拋原本例外 |
| `@rate_limit(calls, period)` | 限制 *period* 秒內最多 *calls* 次；超限拋 `RuntimeError` |

```python
from hyper_framework import emit_metric, watchdog_ping, health_check, alert_on_failure, rate_limit

heartbeat: dict = {}

@emit_metric("api.fetch_users")
def fetch_users(): ...   # [METRIC] api.fetch_users=0.0042s

@watchdog_ping(heartbeat, key="worker")
def process_batch(batch): ...   # heartbeat["worker"] = time.time()

@health_check(on_failure=lambda e: logger.error(str(e)))
def check_db():
    db.ping()   # 回傳 True / False，不拋例外

@alert_on_failure(on_alert=lambda e: send_slack_alert(str(e)))
def critical_job(): ...   # 例外時先通報再重拋

@rate_limit(calls=10, period=60)
def send_email(): ...   # 每分鐘最多 10 次
```

---

### AI Training — 訓練 / 推論生命週期

| 裝飾器 | 說明 |
|---|---|
| `@training_step` | 印出步驟 header/footer，例外加上 `[TRAIN STEP FAILED]` 前綴再重拋 |
| `@log_epoch` | 從引數取得 `epoch`，回傳值若為 dict 則印出各指標 |
| `@inference_only` | `self.training` 為 `True` 時拋 `RuntimeError`（PyTorch-style）|
| `@cache_predictions(maxsize)` | LRU 快取推論結果（以引數為 key）|
| `@grad_check` | 梯度傳播後警告 NaN / Inf（需 `self.parameters()`，PyTorch-style）|

```python
from hyper_framework import training_step, log_epoch, inference_only, cache_predictions

class Trainer:
    @training_step
    def train_batch(self, batch):
        loss = self.forward(batch)
        loss.backward()
        return loss.item()

    @log_epoch
    def run_epoch(self, epoch, loader):
        ...
        return {"loss": 0.42, "acc": 0.91}  # 自動印出：[EPOCH 1] loss=0.4200  acc=0.9100

class Model:
    training = False

    @inference_only
    def predict(self, x): ...   # training=True 時拋 RuntimeError

    @cache_predictions(maxsize=256)
    def embed(self, text): ...   # 相同 text 只推論一次
```

---

### Architecture — SRP / 層次邊界 / 介面合約

| 裝飾器 | 說明 |
|---|---|
| `@single_responsibility(role)` | 在類別 / 函式上標記唯一職責，存為 `__srp_role__` |
| `@layer(name, allowed_imports)` | 標記所屬架構層，存為 `__arch_layer__` |
| `@interface_method` | 標記公開介面合約，存為 `func.__is_interface__ = True` |
| `@abstract_implementation(interface_name)` | 標記具體實作，存為 `func.__implements__` |
| `@no_side_effects` | 宣告純函式，默認只做文件標記（可搭配測試驗證）|
| `@sealed` | 防止子類別繼承（在建立子類別時拋 `TypeError`）|
| `@require_override` | 強制子類別覆寫（呼叫父類實作時拋 `NotImplementedError`）|
| `@enforce_srp` | 若類別方法數超過上限（預設 10）發出 `UserWarning` |

```python
from hyper_framework import (
    single_responsibility, layer, interface_method,
    sealed, require_override, enforce_srp, no_side_effects,
)

@single_responsibility("Parse raw CSV rows into domain records")
@layer("domain")
class CsvParser:
    @interface_method
    def parse(self, raw: str): ...

@sealed
class FinalService:
    pass
# class Sub(FinalService): ...  →  TypeError

class IBase:
    @require_override
    def process(self): ...  # 子類若未覆寫但呼叫父類此方法 → NotImplementedError

@enforce_srp(max_methods=8)
class OverloadedClass:
    ...  # 方法超過 8 個時發出警告

@no_side_effects
def pure_add(a, b): return a + b
```

---

## `helpers.exceptions` — 自訂例外

所有例外可直接從頂層匯入：

```python
from hyper_framework import WrongOptionException, ValidationError, DataLoadError, ...
```

---

### 原有例外（向下相容，API 不變）

| 例外 | 說明 |
|---|---|
| `WrongOptionException(option)` | 傳入無效的選項值 |
| `WrongImplementationException(restriction)` | 違反使用規範 |
| `UnhandledConditionError(state, value)` | 條件未被處理（未知狀態）|
| `RepeatedInitializationError()` | 物件被重複初始化 |

```python
from hyper_framework import (
    WrongOptionException, WrongImplementationException,
    UnhandledConditionError, RepeatedInitializationError,
)

raise WrongOptionException(option="mode_x")
raise WrongImplementationException(restriction="不可在 __init__ 中呼叫")
raise UnhandledConditionError(state=current_state, value=val)
raise RepeatedInitializationError()
```

---

### Lifecycle — 生命週期

| 例外 | 說明 |
|---|---|
| `NotInitializedError(target)` | 物件尚未初始化就被使用 |
| `AlreadyDisposedError(target)` | 已被銷毀的物件被再度使用 |
| `TeardownError(target, reason)` | 清理 / 關閉流程中發生錯誤 |

---

### Options — 選項 / 設定管理

| 例外 | 說明 |
|---|---|
| `MissingOptionError(key)` | 必要選項缺失 |
| `OptionConflictError(keys)` | 互斥選項同時被設定 |
| `OptionReadOnlyError(key)` | 嘗試修改唯讀選項 |
| `InvalidOptionValueError(key, value)` | 選項值不在允許範圍內 |

---

### Architecture — 架構設計違反

| 例外 | 說明 |
|---|---|
| `AbstractMethodNotImplementedError(method)` | 抽象方法未被子類覆寫 |
| `InterfaceContractError(interface, method)` | 未正確實作介面合約 |
| `CircularDependencyError(components)` | 偵測到循環依賴 |
| `ComponentNotRegisteredError(component)` | 元件尚未在容器中註冊 |
| `ComponentAlreadyRegisteredError(component)` | 元件已存在，不允許重複註冊 |
| `LayerViolationError(src_layer, dst_layer)` | 違反層次邊界（如 domain 直接依賴 infra）|

---

### Flow Control — 流程控制

| 例外 | 說明 |
|---|---|
| `ConditionNotMetError(condition)` | 前置條件未滿足 |
| `ExecutionOrderError(expected, actual)` | 執行順序錯誤 |
| `FlowInterruptedError(step)` | 流程被中途中斷 |
| `PipelineCancelledError(pipeline)` | 管線被主動取消 |
| `StepAbortedError(step, reason)` | 單一步驟中止 |
| `MaxIterationsExceededError(limit)` | 已達最大迭代次數 |

---

### Validation — 驗證

| 例外 | 說明 |
|---|---|
| `ConfigurationError(key)` | 設定值缺失或無效 |
| `ValidationError(field, reason)` | 輸入資料驗證失敗 |

---

### Runtime — 運行時

| 例外 | 說明 |
|---|---|
| `TimeoutExpiredError(operation, seconds)` | 操作超時 |
| `DependencyError(dependency)` | 缺少必要的外部依賴 |
| `ReadOnlyError(target)` | 嘗試修改唯讀資源 |
| `StateError(current_state, expected_state)` | 物件處於不正確的狀態 |
| `FeatureNotSupportedError(feature)` | 功能不支援 |
| `ResourceExhaustedError(resource)` | 資源池或配額已耗盡 |

---

### ETL — 管線

| 例外 | 說明 |
|---|---|
| `DataExtractionError(source, reason)` | 資料擷取失敗 |
| `DataTransformationError(step, reason)` | 轉換步驟失敗 |
| `DataLoadError(target, reason)` | 資料載入失敗 |
| `SchemaValidationError(field, expected)` | Schema 不符 |
| `MissingColumnError(column, source)` | 缺少必要欄位 |
| `DataTypeConversionError(column, from_type, to_type)` | 型別轉換失敗 |
| `DuplicateRecordError(key)` | 偵測到重複資料 |
| `EmptyDatasetError(source)` | 資料集為空 |
| `DataCorruptionError(source, reason)` | 資料損毀 |
| `PartitionError(partition, reason)` | 分區操作失敗 |

---

### GUI — 介面操作

| 例外 | 說明 |
|---|---|
| `WidgetNotFoundError(widget_id)` | 找不到指定的 UI 元件 |
| `UIStateError(expected_state, actual_state)` | UI 處於不正確的狀態 |
| `RenderError(component, reason)` | 渲染失敗 |
| `EventHandlerError(event, reason)` | 事件處理器執行失敗 |
| `LayoutError(component, reason)` | 版面計算失敗 |
| `ThemeNotFoundError(theme_name)` | 找不到指定的主題 |
| `WindowNotOpenError(window_id)` | 視窗尚未開啟 |
| `ScreenResolutionError(required, actual)` | 螢幕解析度不足 |

---

### Monitoring — 監察 / 觀測

| 例外 | 說明 |
|---|---|
| `MetricCollectionError(metric, reason)` | 指標收集失敗 |
| `ThresholdExceededError(metric, threshold, actual)` | 指標超過閾值 |
| `WatchdogTriggeredError(watchdog_name)` | Watchdog 偵測到異常 |
| `HealthCheckFailedError(component, reason)` | 健康檢查失敗 |
| `ProbeTimeoutError(probe, timeout)` | 探針逾時 |
| `ObservabilityError(component, reason)` | 觀測系統自身發生錯誤 |
| `SamplingError(metric, reason)` | 取樣失敗 |

---

### AI Training — ML 訓練

| 例外 | 說明 |
|---|---|
| `ModelNotFittedError(model)` | 模型尚未訓練就被用於推論 |
| `CheckpointNotFoundError(path)` | 找不到指定的 checkpoint 檔案 |
| `TrainingInterruptedError(epoch, reason)` | 訓練流程被中斷 |
| `HyperparameterError(param, value, reason)` | 超參數值不合法 |
| `DatasetSplitError(reason)` | 資料集切分失敗 |
| `GradientExplosionError(layer, norm)` | 梯度爆炸 |
| `GradientVanishingError(layer, norm)` | 梯度消失 |
| `InferenceError(model, reason)` | 推論過程中發生錯誤 |
| `EpochLimitReachedError(max_epochs)` | 已達最大 epoch 數 |
| `ModelArchitectureError(reason)` | 模型架構定義有誤 |

```python
from hyper_framework import (
    # lifecycle
    NotInitializedError, AlreadyDisposedError, TeardownError,
    # options
    MissingOptionError, OptionConflictError, InvalidOptionValueError,
    # architecture
    CircularDependencyError, LayerViolationError,
    # flow control
    PipelineCancelledError, MaxIterationsExceededError,
    # validation
    ValidationError, ConfigurationError,
    # runtime
    TimeoutExpiredError, ResourceExhaustedError,
    # ETL
    DataLoadError, SchemaValidationError, EmptyDatasetError,
    # GUI
    WidgetNotFoundError, UIStateError,
    # monitoring
    ThresholdExceededError, HealthCheckFailedError,
    # AI training
    ModelNotFittedError, GradientExplosionError,
)
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


