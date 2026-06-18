# `monitoring` — 迴圈計時器與進度條

提供三個工具讓你輕鬆監控迴圈或多工任務的執行進度、ETA、平均耗時。

## 安裝

無額外依賴，包含於核心套件：

```bash
pip install isd-py-framework-sdk
```

## 架構設計

```
monitoring/
└── looped_function_timer.py
    ├── LoopedFunctionTimer               單進程迴圈計時器（主類別）
    ├── MultiProcessLoopedFunctionTimer   多工版本，繼承自 LoopedFunctionTimer
    ├── LoopedFunction_timer_decorator    自動計時的 method 裝飾器
    ├── ProgressState                     進度狀態 dataclass（傳給 message_maker）
    ├── ProgressLoggerProtocol            自訂 logger 需滿足的 Protocol
    ├── SimpleTerminalLogger              內建輕量 logger（預設，不依賴 SingletonSystemLogger）
    └── ColorLiteral                      顏色名稱的 Literal 型別
```

**解耦設計：** `monitoring` 模組完全不依賴 `SingletonSystemLogger`。預設使用內建的 `SimpleTerminalLogger`（以 ANSI 色碼直接 `print()`），若需要完整日誌功能（帶 timestamp、多 adapter 輸出），可自行傳入任意滿足 `ProgressLoggerProtocol` 的 logger（例如 [message_logger](../message_logger/README.md) 的 `SingletonSystemLogger`）。

## `LoopedFunctionTimer` — 單進程計時器

```python
from isd_py_framework_sdk.monitoring import LoopedFunctionTimer

total = 100
timer = LoopedFunctionTimer(total=total, inline=True, color="cyan")

for i in range(total):
    timer.start()
    # ... 你的工作 ...
    timer.stop()
    timer.msg(i + 1, bar=True)

timer.show_info()
```

**建構參數：**

| 參數 | 型別 | 預設 | 說明 |
|---|---|---|---|
| `total` | `int \| None` | `None` | 總任務數（`msg()` 與 ETA 計算需要） |
| `inline` | `bool` | `True` | `True` = `\r` 覆寫同行；`False` = 每次換行 |
| `level` | `LogLevelLiteral` | `"INFO"` | 非 inline 模式傳給 logger 的等級 |
| `color` | `ColorLiteral` | `"reset"` | 進度條填充色（`"cyan"`, `"green"`, `"yellow"` 等） |
| `logger` | `ProgressLoggerProtocol \| None` | `None` → 使用 `SimpleTerminalLogger` | 自訂 logger（可傳入 `SingletonSystemLogger`） |
| `message_maker` | `Callable \| None` | `None` → 使用內建格式 | 完全自訂進度訊息格式 |

**主要方法：**

| 方法 | 說明 |
|---|---|
| `start()` | 開始計時 |
| `stop()` | 停止計時，記錄本次耗時 |
| `restart(b_do_reset=False)` | `stop()` → （可選 `reset()`）→ `start()` |
| `msg(processed, bar=True)` | 輸出進度條（inline 或換行） |
| `last_msg(bar=True)` | 強制輸出最終 100% 進度 |
| `end_msg()` | 輸出 `✅ DONE !!` |
| `show_info()` | 輸出任務摘要（總耗時、平均耗時） |
| `reset()` | 清空計時記錄 |
| `reset_total(total)` | 更新總任務數 |
| `eta(processed)` | 回傳估算剩餘秒數 |

**計算屬性：**

| 屬性 | 說明 |
|---|---|
| `count` | 已完成次數（`stop()` 的次數） |
| `avg` | 平均單次耗時（秒） |
| `sum` | 累計總耗時（秒） |
| `last` | 最後一次耗時（秒） |

**Context manager 用法：**

```python
with LoopedFunctionTimer(total=n) as timer:
    # start() / stop() 由 __enter__ / __exit__ 自動呼叫
    pass
```

## `LoopedFunction_timer_decorator` — 方法自動計時裝飾器

需求：**class 上必須有 `self.timer` 屬性**（`LoopedFunctionTimer` 實例）。

```python
from isd_py_framework_sdk.monitoring import (
    LoopedFunctionTimer,
    LoopedFunction_timer_decorator,
)

class TaskProcessor:
    def __init__(self, total: int):
        self.timer = LoopedFunctionTimer(total=total)

    @LoopedFunction_timer_decorator
    def process(self, task_id: int):
        # ... 你的工作 ...
        return f"done {task_id}"

    def run(self):
        for i in range(20):
            self.process(i)
        self.timer.show_info()
```

裝飾器會在每次呼叫時自動執行 `timer.start()` → 原函式 → `timer.stop()` → `timer.msg()`。

## `MultiProcessLoopedFunctionTimer` — 多工計時器

適用於 `ProcessPoolExecutor` / `ThreadPoolExecutor` 的 `as_completed()` 主迴圈。

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
from isd_py_framework_sdk.monitoring import MultiProcessLoopedFunctionTimer

def heavy(i):
    import time; time.sleep(0.01)
    return i

total = 10000
timer = MultiProcessLoopedFunctionTimer(total=total, inline=True, color="green")

with ProcessPoolExecutor() as executor:
    futures = {executor.submit(heavy, i): i for i in range(total)}
    timer.start()
    for future in as_completed(futures):
        future.result()
        timer.task_completed(b_show_msg=True, bar=True)
    timer.stop()

timer.show_info()
```

**專屬方法：**

| 方法 | 說明 |
|---|---|
| `task_completed(b_show_msg, **kwargs)` | 通知一個任務完成，自動節流更新 |
| `batched_task_completed(batch_size, b_show_msg, **kwargs)` | 一次通知多個任務完成 |

> **節流機制：** 預設每完成 1%（最多 10,000）任務才更新一次顯示，避免過多 I/O。

## 自訂 Logger（進階）

任何滿足 `ProgressLoggerProtocol` 的物件都可以傳入：

```python
from isd_py_framework_sdk.monitoring import LoopedFunctionTimer, ProgressLoggerProtocol
from isd_py_framework_sdk.message_logger import SingletonSystemLogger, DarkThemeTerminalAdapter

# 方法 A：使用 SingletonSystemLogger（完整功能：timestamp、多 adapter）
logger = SingletonSystemLogger()
logger.register_adapter(DarkThemeTerminalAdapter("CHECKPOINT"))
timer = LoopedFunctionTimer(total=100, logger=logger, level="CHECKPOINT")

# 方法 B：完全自訂（滿足 Protocol 即可）
class MyLogger:
    def log(self, msg: str, level: str) -> None: print(f"[{level}] {msg}")
    def info(self, msg: str) -> None: print(msg)
    def success(self, msg: str) -> None: print(f"✅ {msg}")
    def flush(self) -> None: pass

timer = LoopedFunctionTimer(total=100, logger=MyLogger())
```

## 自訂訊息格式（`message_maker`）

```python
from isd_py_framework_sdk.monitoring import LoopedFunctionTimer, ProgressState

def my_maker(state: ProgressState, bar_len: int, use_bar: bool) -> str:
    pct = state.processed / state.total * 100
    return f"[{pct:5.1f}%] elapsed={state.total_time:.2f}s"

timer = LoopedFunctionTimer(total=100, message_maker=my_maker)
```

## 顏色選項（`ColorLiteral`）

`"red"`, `"green"`, `"yellow"`, `"blue"`, `"magenta"`, `"purple"`, `"cyan"`, `"sky_blue"`, `"white"`, `"gray"`, `"reset"`

## Import 方式

```python
from isd_py_framework_sdk.monitoring import (
    LoopedFunctionTimer,
    MultiProcessLoopedFunctionTimer,
    LoopedFunction_timer_decorator,
    ProgressState,
    ProgressLoggerProtocol,
    SimpleTerminalLogger,
    ColorLiteral,
)
```

## 支援情境一覽

以下五種情境均經過驗證，代表套件在各場景下的正確性。

| 情境 | 核心 API | 說明 |
|---|---|---|
| 一、單進程 for 迴圈 | `start` / `stop` / `msg` / `show_info` | inline 進度條覆寫同行，含 ETA 與顏色 |
| 二、裝飾器自動計時 | `@LoopedFunction_timer_decorator` | 自動計時 class method，無需手動 start/stop |
| 三、多工 as_completed | `task_completed` | ProcessPoolExecutor + as_completed，任務無序完成，進度計數正確 |
| 四、雙重迴圈節流 | `task_completed` + `wait(FIRST_COMPLETED)` | 外層高成本初始化 + 內層逐一提交；節流防止佇列爆炸 |
| 五、雙重迴圈批次節流 | `batched_task_completed` + `wait(FIRST_COMPLETED)` | 內層打包批次後提交；批次節流減少 IPC overhead |

完整可執行範例見 `examples/monitoring/different_usecase.py`（下載原始碼後可直接執行）：

```powershell
.venv\Scripts\python.exe examples/monitoring/different_usecase.py
```

---

開發/架構細節請見 [agent.md](agent.md)。
