# agent.md — `unified_io` 套件

## ⚠️ 目前狀態：非功能性 stub（2026-06 重新驗證）

實際檢查 `adapters/` 下的檔案後發現**目前整個套件無法被 import**：

| 檔案 | 大小 | 狀態 |
|---|---|---|
| `csv_adapter.py` | 0 bytes | 完全空白，`CsvIOAdapter` 不存在 |
| `json_adapter.py` | 0 bytes | 完全空白，`JsonIOAdapter` 不存在 |
| `sql_adapter.py` | 0 bytes | 完全空白，`SqlIOAdapter` 不存在 |
| `excel_adapter.py` | 443 bytes | 只有 `class ExcelIOAdapter(IIOAdapter):` 簽名，**沒有 class body** → `IndentationError`（已用 `python -m py_compile` 確認） |

而 `adapters/__init__.py` 對這四個全部執行 `from .xxx_adapter import XxxIOAdapter`，所以**任何** `from isd_py_framework_sdk.unified_io.adapters import ...` 都會在載入 `excel_adapter.py` 時就因 `IndentationError` 失敗（在它失敗之前，`csv_adapter`/`json_adapter`/`sql_adapter` 本來就會因為 `ImportError: cannot import name 'XxxIOAdapter'` 失敧）。

**修改任何使用此套件的程式碼前，務必先確認這個狀態是否已經改變**（重新跑一次 `python -m py_compile src/isd_py_framework_sdk/unified_io/adapters/*.py`）。下面的「核心介面」與「具體 Adapter」章節描述的是**設計意圖**（從 `_interface.py` 與檔案/extras 命名推斷），不是目前可執行的程式碼。

---

## 職責（設計意圖）

提供統一的資料 IO 介面（`IReader` / `IWriter`），讓上層業務邏輯不需關心底層格式（CSV、Excel、JSON、SQL），只需操作 `pandas.DataFrame`。

**注意：** 此套件目前尚在早期階段，沒有對應的 `__init__.py` 在 `isd_py_framework_sdk` 根層匯出（只有 `pyproject.toml` 中的 extras 定義，但根 `__init__.py` 沒有匯入它）。需要直接從 `isd_py_framework_sdk.unified_io` import。

---

## 架構

```
unified_io/
├── .env                           環境設定（不版控，不應 commit）
└── adapters/
    ├── __init__.py               匯出 CsvIOAdapter, ExcelIOAdapter, JsonIOAdapter, SqlIOAdapter
    ├── _interface.py             IReader, IWriter, IIOAdapter（ABC 定義）
    ├── csv_adapter.py            CsvIOAdapter
    ├── excel_adapter.py          ExcelIOAdapter
    ├── json_adapter.py           JsonIOAdapter
    └── sql_adapter.py            SqlIOAdapter
```

---

## 核心介面

```python
from isd_py_framework_sdk.unified_io.adapters._interface import IReader, IWriter, IIOAdapter
import pandas as pd
from pathlib import Path

class IReader(ABC):
    def read(self, source: str | Path | Any, **kwargs) -> pd.DataFrame: ...

class IWriter(ABC):
    def write(self, df: pd.DataFrame, destination: str | Path | Any, **kwargs) -> None: ...

class IIOAdapter(IReader, IWriter, ABC): ...
```

所有 adapter 皆以 `pd.DataFrame` 作為中間格式，讓讀/寫的資料型別統一。

---

## 具體 Adapter

```python
from isd_py_framework_sdk.unified_io.adapters import (
    CsvIOAdapter,
    ExcelIOAdapter,
    JsonIOAdapter,
    SqlIOAdapter,
)
```

| Adapter | 讀來源 | 寫目標 | 需要 extras |
|---|---|---|---|
| `CsvIOAdapter` | CSV 檔案路徑 | CSV 檔案路徑 | `[unified_io]`（pandas）|
| `ExcelIOAdapter` | xlsx 路徑 | xlsx 路徑 | `[unified_io.excel]`（pandas + openpyxl）|
| `JsonIOAdapter` | JSON 檔案路徑 | JSON 檔案路徑 | `[unified_io]`（pandas）|
| `SqlIOAdapter` | SQL query string | table name | `[unified_io.sql]`（pandas + sqlalchemy）|

---

## 使用範例（⚠️ 設計意圖，目前無法執行 — 見上方狀態章節）

```python
from isd_py_framework_sdk.unified_io.adapters import CsvIOAdapter, ExcelIOAdapter
from pathlib import Path

# 讀取
adapter = CsvIOAdapter()
df = adapter.read("data/input.csv")

# 寫入
adapter.write(df, Path("data/output.csv"))

# 使用 IIOAdapter 泛型介面
from isd_py_framework_sdk.unified_io.adapters._interface import IIOAdapter

def process(adapter: IIOAdapter, src: Path, dst: Path):
    df = adapter.read(src)
    # ... transform ...
    adapter.write(df, dst)
```

---

## 依賴 Extras

```bash
# 核心（CSV + JSON）
pip install isd-py-framework-sdk[unified_io]

# Excel 後端
pip install isd-py-framework-sdk["unified_io.excel"]

# SQL 後端
pip install isd-py-framework-sdk["unified_io.sql"]
```

---

## `.env` 檔案

`unified_io/.env` 是 SQL adapter 的連線字串等機密設定，**不應版控**（已在 `.gitignore` 中）。`.env.need_to_be_ignore` 在根目錄是提醒佔位符。

---

## 擴充新格式

1. 在 `adapters/` 下新增 `<format>_adapter.py`
2. 繼承 `IIOAdapter`，實作 `read()` 和 `write()`
3. 在 `adapters/__init__.py` 匯出
4. 若有外部依賴，在 `pyproject.toml` 新增 extras

---

## 常見陷阱

- **最重要：`adapters/__init__.py` 目前無法被 import**（見頂部狀態章節），任何依賴 `unified_io.adapters` 的程式碼都會在 import 階段就失敗。在這裡投入開發時間前，先確認此狀態。
- `pandas` 是所有 adapter 的必要依賴，未安裝時 import 就會失敗（不是 lazy 的）
- `unified_io` 目前沒有 pytest 測試檔（尚未完善測試覆蓋）——這與上述空檔案狀態相符，暗示此套件從未被完整實作或測試過
- 根層 `__init__.py` **不**匯出 `unified_io` 的任何內容，必須直接用完整路徑 import
