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

### `SingletonSystemLogger`

全域單例彩色日誌系統，支援等級過濾、多輸出模式（console / file / tkinter widget）。

**Log Levels（由低到高）：**

| Level | 用途 |
|---|---|
| `DEBUG` | 開發時詳細追蹤資訊 |
| `INFO` | 正常流程資訊 |
| `CHECKPOINT` | 關鍵流程節點 |
| `SUCCESS` | 操作成功 |
| `WARNING` | 潛在問題，不影響運行 |
| `ERROR` | 操作失敗，需修正 |
| `CRITICAL` | 致命錯誤，系統無法繼續 |
| `HIGHLIGHT` | 超醒目標記 |

```python
from hyper_framework import SingletonSystemLogger

logger = SingletonSystemLogger()

# 基本用法
logger.log("系統啟動完成", level="INFO")
logger.log("資料載入成功", level="SUCCESS")
logger.shiny_log("關鍵里程碑", level="CHECKPOINT")

# 設定
logger.set_min_level("WARNING")   # 只顯示 WARNING 以上
logger.set_output_mode("both")    # 同時輸出 console + file
logger.set_log_file("app.log")
logger.disable()                  # 暫停輸出
logger.enable()

# tkinter 整合（選用）
# logger.set_window(my_text_widget)
```

**環境變數控制：**
- `RUN_MODE=DEBUG`（預設） — 顯示所有等級
- `RUN_MODE=DISPLAY` — 顯示 INFO 以上
- `RUN_MODE=RUN` — 僅顯示 ERROR
- `CONSOLE_BG=light|dark` — 調整 console 顏色主題

---

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


