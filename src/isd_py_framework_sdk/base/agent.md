# agent.md — `base` 套件

## 職責

提供整個框架的核心設計模式基礎，目前僅包含一個核心元件：`SingletonMetaclass`。

---

## 架構

```
base/
├── Singleton.py    SingletonMetaclass（元類）
├── __init__.py     匯出 SingletonMetaclass
├── exp01.py        實驗用（開發草稿，非正式 API）
└── exp02.py        實驗用（開發草稿，非正式 API）
```

---

## `SingletonMetaclass`

### 設計機制

`SingletonMetaclass` 繼承自 Python 內建 `type`，覆寫 `__call__`。它維護一個類別層級的字典 `_instances: Dict[Type, Any]`，每個 **類別**（不是物件）為 key，第一次建立的實例為 value。

```python
class SingletonMetaclass(type):
    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            if hasattr(instance, '_initialize_manager'):
                instance._initialize_manager()   # 一次性初始化鉤子
            cls._instances[cls] = instance
        return cls._instances[cls]
```

**注意**：`_instances` 是類別屬性（class-level），所有以 `SingletonMetaclass` 為 metaclass 的類別共享同一個字典，但以不同的 `cls` 為 key，因此互不干擾。

### `_initialize_manager` 鉤子

若子類定義了 `_initialize_manager(self)` 方法，它會在實例**首次建立**後自動呼叫一次。這是用來替代在 `__init__` 中寫初始化邏輯的推薦方式（因為 singleton 的 `__init__` 每次 `MyClass()` 都會被呼叫，但 `_initialize_manager` 只跑一次）。

```python
from isd_py_framework_sdk.interface import SingletonMetaclass

class MyManager(metaclass=SingletonMetaclass):
    def _initialize_manager(self):
        self._data = []       # 只初始化一次
    
    def add(self, item):
        self._data.append(item)

a = MyManager()
b = MyManager()
assert a is b  # True
```

### 與 ABC 共用

`path_manager` 使用 `_meta.py` 中的 `SingletonABCMeta`（組合 `ABCMeta + SingletonMetaclass`），以解決 ABC + singleton metaclass 衝突問題。若你需要讓 singleton 也繼承 ABC，參考 `path_manager/_meta.py` 的實作方式。

---

## 進入點與 Import

```python
# 推薦路徑
from isd_py_framework_sdk.interface import SingletonMetaclass

# 或直接引用
from isd_py_framework_sdk.base import SingletonMetaclass
from isd_py_framework_sdk.base.Singleton import SingletonMetaclass
```

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/base/singleton_test.py
```

---

## 常見陷阱

- **不要**在 `__init__` 做一次性初始化邏輯——改用 `_initialize_manager`。
- `exp01.py` / `exp02.py` 是開發過程中的實驗草稿，不屬於公開 API，未來可能隨時移除。
