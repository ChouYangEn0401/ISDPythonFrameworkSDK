# `base` — 核心設計模式

提供 `SingletonMetaclass`：一個元類（metaclass），讓任何類別自動實現執行緒安全的單例（Singleton）模式，是整個 SDK（`message_logger`、`path_manager`、`events` 等）共用的基石。

## 安裝

無額外依賴，包含於核心套件：

```bash
pip install isd-py-framework-sdk
```

## 快速開始

```python
from isd_py_framework_sdk.interface import SingletonMetaclass

class MyManager(metaclass=SingletonMetaclass):
    def _initialize_manager(self):
        # 單例首次建立時自動執行一次
        self.data = []

a = MyManager()
b = MyManager()
assert a is b  # True，永遠回傳同一個實例
```

## 特性

- **執行緒安全**：內部以鎖保護首次建立流程，避免多執行緒同時建立出兩個實例。
- **可選初始化鉤子**：若類別定義了 `_initialize_manager(self)`，會在第一次建立實例後自動呼叫一次；後續呼叫 `MyManager()` 不會再觸發。
- **零侵入**：只需要 `metaclass=SingletonMetaclass`，不需要修改 `__init__` 或額外撰寫單例樣板程式碼。

## Import 方式

```python
# 建議：透過短路徑別名
from isd_py_framework_sdk.interface import SingletonMetaclass

# 或直接引用實體模組
from isd_py_framework_sdk.base.Singleton import SingletonMetaclass
```

## 適用場景

任何專案內「全域只應存在一個實例」的物件都適合使用，例如設定管理者、連線池、快取、本 SDK 自己的 `SingletonSystemLogger`（[message_logger](../message_logger/README.md)）與 `SingletonPathManager`（[path_manager](../path_manager/README.md)）。

---

開發/架構細節請見 [agent.md](agent.md)。
