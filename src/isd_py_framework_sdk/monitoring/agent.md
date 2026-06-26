# agent.md — `monitoring` 套件

## 職責

提供迴圈計時器與進度條，讓長時間的批次任務（for 迴圈、多進程 executor）能顯示即時進度、ETA 與統計摘要，且**完全不依賴** `SingletonSystemLogger`。

---

## 架構

```
monitoring/
├── looped_function_timer.py    全部實作（單一檔案）
│   ├── ColorLiteral            顏色名稱 Literal 型別
│   ├── _SimpleTerminalLogger   內建輕量 logger（ANSI 直接 print）
│   ├── ProgressLoggerProtocol  自訂 logger 需滿足的 Protocol
│   ├── ProgressState           進度狀態 dataclass
│   ├── LoopedFunctionTimer     主要計時器（單進程）
│   ├── MultiProcessLoopedFunctionTimer  多工版本
│   └── LoopedFunction_timer_decorator   class method 自動計時裝飾器
└── __init__.py                 全部公開 API 匯出
```

---

## 三個工具

### 1. `LoopedFunctionTimer`（單進程計時器）

適用於一般 `for` 迴圈。

```python
from isd_py_framework_sdk.monitoring import LoopedFunctionTimer

total = 100
timer = LoopedFunctionTimer(total=total, inline=True, color="cyan")

for i in range(total):
    timer.start()
    # ... 工作 ...
    timer.stop()
    timer.msg(i + 1, bar=True)

timer.show_info()   # 印出摘要（總耗時、平均）
```

**Context manager 用法：**
```python
with LoopedFunctionTimer(total=n) as timer:
    pass   # __enter__ 自動 start()，__exit__ 自動 stop()
```

**建構參數：**

| 參數 | 型別 | 預設 | 說明 |
|---|---|---|---|
| `total` | `int \| None` | `None` | 總任務數 |
| `inline` | `bool` | `True` | `True` = `\r` 覆寫同行；`False` = 換行 |
| `level` | `LogLevelLiteral` | `"INFO"` | 傳給 logger 的等級（非 inline 模式） |
| `color` | `ColorLiteral` | `"reset"` | 進度條填充色 |
| `logger` | `ProgressLoggerProtocol \| None` | `None`（使用內建） | 自訂 logger |
| `message_maker` | `Callable \| None` | `None`（使用內建格式） | 完全自訂訊息格式 |

**計算屬性：**`count`（完成次數）、`avg`（平均耗時秒）、`sum`（累計秒）、`last`（最後耗時）

**主要方法：**`start()`, `stop()`, `restart(b_do_reset=False)`, `msg(processed, bar=True)`, `last_msg(bar=True)`, `end_msg()`, `show_info()`, `reset()`, `reset_total(total)`, `eta(processed)`

---

### 2. `MultiProcessLoopedFunctionTimer`（多工計時器）

繼承自 `LoopedFunctionTimer`，適用於 `ProcessPoolExecutor` / `ThreadPoolExecutor` + `as_completed()` 模式。

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
from isd_py_framework_sdk.monitoring import MultiProcessLoopedFunctionTimer

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
- `task_completed(b_show_msg, **kwargs)` — 通知一個任務完成，內建節流（預設每完成 1% 才更新顯示）
- `batched_task_completed(batch_size, b_show_msg, **kwargs)` — 批次通知

> **節流機制**：預設每完成 max(1, total//100) 個任務更新一次，最多每 10,000 個任務更新一次。避免高頻 I/O。

---

### 3. `LoopedFunction_timer_decorator`（method 自動計時裝飾器）

要求 class 上必須有 `self.timer` 屬性（`LoopedFunctionTimer` 實例）。裝飾後自動執行 `start() → 原函式 → stop() → msg()`。

```python
from isd_py_framework_sdk.monitoring import LoopedFunctionTimer, LoopedFunction_timer_decorator

class TaskProcessor:
    def __init__(self, total: int):
        self.timer = LoopedFunctionTimer(total=total)

    @LoopedFunction_timer_decorator
    def process(self, task_id: int):
        # ... 工作 ...
        return f"done {task_id}"
```

---

## 自訂 Logger

任何實作 `ProgressLoggerProtocol` 的物件皆可注入：

```python
class ProgressLoggerProtocol(Protocol):
    def log(self, msg: str, level: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def success(self, msg: str) -> None: ...
    def flush(self) -> None: ...
```

可以傳入 `SingletonSystemLogger`（它天然滿足此 Protocol），或完全自訂。

---

## 自訂訊息格式（`message_maker`）

```python
from isd_py_framework_sdk.monitoring import LoopedFunctionTimer, ProgressState

def my_maker(state: ProgressState, bar_len: int, use_bar: bool) -> str:
    pct = state.processed / state.total * 100
    return f"[{pct:5.1f}%] elapsed={state.total_time:.2f}s"

timer = LoopedFunctionTimer(total=100, message_maker=my_maker)
```

`ProgressState` 欄位：`processed`, `total`, `avg_time`, `total_time`, `eta_seconds`, `last_time`

---

## 顏色選項（`ColorLiteral`）

`"red"`, `"green"`, `"yellow"`, `"blue"`, `"magenta"`, `"purple"`, `"cyan"`, `"sky_blue"`, `"white"`, `"gray"`, `"reset"`

---

## 進入點與 Import

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

---

## 測試

```powershell
# 5 種情境完整驗證（非 pytest，直接執行）
.venv\Scripts\python.exe examples/monitoring/different_usecase.py

# pytest 整合測試
.venv\Scripts\python.exe -m pytest -v tests/monitoring/different_usecase_test.py
```

---

## 解耦設計說明

`monitoring` 模組刻意不 import `SingletonSystemLogger`，保持低耦合：
- 預設使用 `_SimpleTerminalLogger`（內建，只依賴標準庫 ANSI codes）
- 需要完整功能（timestamp、多 adapter）時由呼叫端傳入 logger 實例
- 這使得 `monitoring` 可以在不安裝 `[message_logger]` extras 的環境下運作

### 對外橋接依賴（純型別）

`looped_function_timer.py` 唯一碰到 `message_logger` 的地方是型別 `LogLevelLiteral`，且**只用於型別註解、執行期完全不需要**。因此它走 `from __future__ import annotations` + `if TYPE_CHECKING:` import，**runtime 完全沒有 import `message_logger`**（見 [`interop/agent.md`](../interop/agent.md) 橋接表 #3）。

| 觸發時機 | 被用到的子套件 | 需要的 extra |
|---|---|---|
| 無 runtime 觸發（純型別 `LogLevelLiteral`） | `message_logger`（型別） | 無 |

因為沒有 runtime 重依賴可缺，這條「橋」不經過 `interop.require_feature`；列入橋接表只是為了帳本完整。

---

## 常見陷阱

- `LoopedFunction_timer_decorator` 要求 class 上存在 `self.timer` 屬性，缺少時 `AttributeError`。
- `MultiProcessLoopedFunctionTimer` 中 `task_completed` 有內部計數器；如果任務總數比 `total` 多或少，進度百分比會錯。
- `message_maker` 若不傳 `total`，`ProgressState.total` 為 `None`，除法會 crash——務必搭配 `total` 參數使用自訂格式。
