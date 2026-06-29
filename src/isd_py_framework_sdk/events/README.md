# `events` — 事件系統

提供 pub/sub（觀察者模式）事件匯流排：定義事件型別、訂閱、取消訂閱、觸發。內建弱引用（weak reference）回呼儲存，避免訂閱關係意外延長物件生命週期造成記憶體洩漏。

## 安裝

無額外依賴，包含於核心套件：

```bash
pip install isd-py-framework-sdk
```

## 定義事件

繼承對應的基底類別：

```python
from isd_py_framework_sdk.events_bus import IEventBase, IParsEventBase
from dataclasses import dataclass

# 無參數事件
class OnDataReady(IEventBase): pass

# 帶參數事件
@dataclass
class OnDataLoaded(IParsEventBase):
    row_count: int
    source: str
```

## `SingletonEventManager` — 全域事件匯流排

負責訂閱（`RegisterEvent`）、取消訂閱（`UnregisterEvent`）、觸發（`TriggerEvent`）。

支援兩種 callback 型別：
- **綁定方法**（bound methods）— 以 `WeakMethod` 保存，不會延長物件生命週期
- **普通 callable**（module-level functions、static methods）— 以 `weakref.ref` 保存

> **lambda 一律被拒絕：** callback 必須是「明確持有」的具名可呼叫物件。傳入 lambda 會在
> `RegisterEvent` 當下直接 `raise TypeError`（不是事後無聲消失）。原因是弱引用會把沒有強引用
> 持有者的匿名 closure 立即 GC 掉，造成無聲失效且無法解除註冊——把規則寫死、省掉逐案推理生命
> 週期的負擔。請改用 `self.method` 或 module-level / static 函式。
>
> **觸發時的錯誤隔離：** 某個 handler 內部拋例外時會被「隔離」——以 ERROR 等級記錄
> （含 traceback，走標準庫 `logging`），但**其他 handler 照常觸發、拋例外的 handler 也不會被
> 退訂**。一個壞訂閱者不會連累其他訂閱者，也不會悄悄消失。

```python
from isd_py_framework_sdk.events_bus import SingletonEventManager, IEventBase, IParsEventBase
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

em.RegisterEvent(OnJobDone, handle_done)
em.TriggerEvent(OnJobDone())
em.UnregisterEvent(OnJobDone, handle_done)

w = Worker()
w.subscribe()
em.RegisterEvent(OnProgress, w.on_inner_progress)
em.TriggerEvent(OnJobDone())
em.TriggerEvent(OnProgress(percent=0.5))
```

**除錯模式：** 設定環境變數 `EVENT_MANAGER_DEBUGGER=1` 可印出詳細的事件類型解析資訊，方便排查訂閱/觸發不匹配的問題。

## `DelayEventBusManager` ⚠️ 未完成功能（`==NEW-STRUCTURE-UNDONE==`）

延遲事件匯流排（Event Replay 模式）。適用場景：訂閱者比發布者**晚初始化**，需要在訂閱後補齊（replay）先前已觸發過的事件。

```python
from isd_py_framework_sdk.events_bus import DelayEventBusManager, IDelayEventBase

class OnSystemReady(IDelayEventBase): pass

bus = DelayEventBusManager()

class LateModule:
    def _initialize(self):
        bus.RegisterEvent(OnSystemReady, self._on_system_ready)
        bus.Evoke(OnSystemReady)   # 補齊之前已觸發過的事件

    def _on_system_ready(self):
        print("Caught up!")
```

> **One-shot 語意：** `Evoke()` 執行後，對應事件的 callback 列表會被清空。
> 此功能設計仍在迭代中，使用前請確認目前版本的行為符合預期。

## `MulticastCallback` — 通用多播集合

把多個處理器（例如：日誌、UI 更新、度量收集）綁在同一個事件上，支持直接呼叫、合併（`+`）、移除（`-`）。

```python
from isd_py_framework_sdk.events_bus import MulticastCallback
from typing import Callable, List

on_progress: MulticastCallback[Callable[[int], None]] = MulticastCallback()

def log_progress(p: int):
    print(f"[LOG] progress={p}/100")

def update_ui(p: int):
    print(f"UI -> Progress bar set to {p}%")

metrics: List[int] = []
def collect_metric(p: int):
    metrics.append(p)

on_progress.add(collect_metric)
on_progress.add(log_progress)
on_progress.add(update_ui)

on_progress(10)   # 廣播給所有已註冊的 handler

# 移除某個 handler（- 回傳新物件，需重新指派）
on_progress = on_progress - update_ui
on_progress(50)

# 合併兩個 MulticastCallback（回傳新物件，不修改原 operands）
extra = MulticastCallback[Callable[[int], None]]()
extra.add(lambda p: print(f"extra handler: {p}"))
combined = on_progress + extra
combined(75)
```

> **注意：** `+` / `-` 運算子回傳新物件；若要修改現有變數，必須把結果重新指派回原變數。

## Import 方式

```python
from isd_py_framework_sdk.events_bus import (
    SingletonEventManager,
    IEventBase,
    IParsEventBase,
    DelayEventBusManager,
    IDelayEventBase,
    MulticastCallback,
)
```

---

開發/架構細節（`_WeakCallable` 實作機制等）請見 [agent.md](agent.md)。
