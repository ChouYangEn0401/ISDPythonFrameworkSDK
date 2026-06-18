# agent.md — `events` 套件

## 職責

提供鬆耦合的事件系統（Observer / Pub-Sub 模式），讓模組之間可以透過事件通訊而不需要直接引用彼此。包含三個獨立元件：即時事件匯流排、延遲回放事件匯流排、多播回調集合。

---

## 架構

```
events/
├── EventBase.py              IEventBase, IParsEventBase（事件基底類別）
├── EventManager.py           SingletonEventManager（即時事件匯流排）
├── DelayEventBase.py         IDelayEventBase, IDelayParsEventBase
├── DelayEventBusManager.py   DelayEventBusManager（延遲回放匯流排）⚠️ 未完成
├── DelayEvents.py            內建延遲事件（保留/實驗）
├── Events.py                 內建事件（保留/實驗）
├── MulticastCallback.py      MulticastCallback（多播回調集合）
└── __init__.py               公開 API 匯出
```

---

## 元件說明

### 1. `SingletonEventManager`（即時事件匯流排）

全域單例，用來訂閱/取消訂閱/觸發事件。

**事件類別定義：**
- 無參數事件：繼承 `IEventBase`
- 帶參數事件：繼承 `IParsEventBase`（通常用 `@dataclass` 定義欄位）

```python
from dataclasses import dataclass
from isd_py_framework_sdk.events import IEventBase, IParsEventBase

class OnJobDone(IEventBase): pass

@dataclass
class OnProgress(IParsEventBase):
    percent: float
```

**API：**
```python
em = SingletonEventManager()
em.RegisterEvent(event_class, callback)
em.UnregisterEvent(event_class, callback)
em.TriggerEvent(event_instance)   # IEventBase → callback()；IParsEventBase → callback(event)
```

**弱引用機制（`_WeakCallable`）：**
`EventManager` 以弱引用保存 callback，避免延長物件生命週期：
- **bound method**（`self.method`）→ `weakref.WeakMethod`
- **plain callable**（module 函式、static method）→ `weakref.ref`

> **Lambda / local closure 警告**：沒有強引用持有者的 callable 訂閱後可能立即被 GC，導致無聲失效。必須由呼叫端保持強引用，或改用 module-level 函式。

**內部存儲：**
兩個獨立的 `defaultdict(list)`：
- `__registered_events`（`IEventBase` 系列）
- `__registered_pars_events`（`IParsEventBase` 系列）

觸發時呼叫完畢後會自動清掃已被 GC 的死引用。

---

### 2. `DelayEventBusManager`（延遲回放匯流排）⚠️

**標記為未完成（NEW-STRUCTURE-UNDONE）**，設計仍在迭代。

用途：訂閱者晚於發布者初始化時，可呼叫 `Evoke(event_class)` 重放已觸發的事件。語意為 **one-shot**：Evoke 後該事件的 callback 清單被清空。

```python
from isd_py_framework_sdk.events import DelayEventBusManager, IDelayEventBase

class OnSystemReady(IDelayEventBase): pass
bus = DelayEventBusManager()

# 先觸發
bus.TriggerEvent(OnSystemReady())

# 晚初始化的模組：訂閱後立即 replay
bus.RegisterEvent(OnSystemReady, self._on_ready)
bus.Evoke(OnSystemReady)   # 補齊先前觸發過的事件
```

---

### 3. `MulticastCallback`（多播回調集合）

通用、可組合的 callback 集合（非事件匯流排，不是 singleton）。適合把多個 handler 綁在同一個 hook 上（如進度更新同時通知 log、UI、metrics）。

```python
from typing import Callable
from isd_py_framework_sdk.events import MulticastCallback

on_progress: MulticastCallback[Callable[[int], None]] = MulticastCallback()

on_progress.add(log_progress)
on_progress.add(update_ui)
on_progress(50)                       # 廣播給全部 handler

# 不可變運算子
on_progress = on_progress - update_ui  # 移除，回傳新物件
combined = on_progress + extra         # 合併，回傳新物件
```

`+` / `-` 運算子不修改原物件，均回傳新的 `MulticastCallback`；若要生效須重新指派。

---

## 進入點與 Import

```python
# 推薦路徑
from isd_py_framework_sdk.events import (
    IEventBase, IParsEventBase,
    SingletonEventManager,
    IDelayEventBase, IDelayParsEventBase,
    DelayEventBusManager,
    MulticastCallback,
)

# 短路徑別名（向下相容）
from isd_py_framework_sdk.events_bus import SingletonEventManager, IEventBase, ...
```

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/events/event_test.py
.venv\Scripts\python.exe -m pytest -v tests/events/multicallbacks.py
.venv\Scripts\python.exe -m pytest -v tests/events/delay_test.py
```

---

## 除錯

設定 `EVENT_MANAGER_DEBUGGER=1` 環境變數，`SingletonEventManager` 會在每次事件分發時印出詳細的型別 ID / MRO 資訊，適合診斷「不同 import 路徑導致型別不匹配」問題。

---

## 常見陷阱

- `RegisterEvent`/`UnregisterEvent` 第一個參數必須是**類別本身**（e.g. `OnJobDone`），不是實例。
- `TriggerEvent` 第一個參數是**實例**（e.g. `OnJobDone()`）。
- 同一個 callback 只能在弱引用有效時被調用；GC 後會被靜默清掃（並印出 warning）。
