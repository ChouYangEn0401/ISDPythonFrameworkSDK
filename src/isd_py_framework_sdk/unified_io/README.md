# `unified_io` — 統一資料 IO 介面

## ⚠️ 目前狀態：開發中（尚不可用）

這個套件目前是**未完成的 stub**：`adapters/` 下除了 `_interface.py` 之外，`csv_adapter.py`、`json_adapter.py`、`sql_adapter.py` 都是空檔案，`excel_adapter.py` 只有 class 簽名沒有實作內容。換句話說，目前 `from isd_py_framework_sdk.unified_io.adapters import ...` **會直接失敗**，不論是哪一個 adapter。

如果你正在尋找可用的資料讀寫工具，目前請改用：
- 直接使用 `pandas` 的 `read_csv` / `read_excel` / `to_sql` 等原生 API。
- 比對檔案內容（而非讀寫）可以參考 [file_compare](../file_compare/README.md)。

以下內容描述的是**設計目標**，供未來實作此套件時參考。

## 設計目標

提供統一的資料 IO 介面（`IReader` / `IWriter`），讓上層業務邏輯不需關心底層格式（CSV、Excel、JSON、SQL），只需操作 `pandas.DataFrame`：

```python
from isd_py_framework_sdk.unified_io.adapters._interface import IReader, IWriter, IIOAdapter

class IReader(ABC):
    def read(self, source: str | Path | Any, **kwargs) -> pd.DataFrame: ...

class IWriter(ABC):
    def write(self, df: pd.DataFrame, destination: str | Path | Any, **kwargs) -> None: ...

class IIOAdapter(IReader, IWriter, ABC): ...
```

計畫中的具體 adapter：

| Adapter | 讀來源 | 寫目標 | 需要 extras |
|---|---|---|---|
| `CsvIOAdapter` | CSV 檔案路徑 | CSV 檔案路徑 | `[unified_io]`（pandas）|
| `ExcelIOAdapter` | xlsx 路徑 | xlsx 路徑 | `[unified_io.excel]`（pandas + openpyxl）|
| `JsonIOAdapter` | JSON 檔案路徑 | JSON 檔案路徑 | `[unified_io]`（pandas）|
| `SqlIOAdapter` | SQL query string | table name | `[unified_io.sql]`（pandas + sqlalchemy）|

預期使用方式（一旦實作完成）：

```python
from isd_py_framework_sdk.unified_io.adapters import CsvIOAdapter
from pathlib import Path

adapter = CsvIOAdapter()
df = adapter.read("data/input.csv")
adapter.write(df, Path("data/output.csv"))
```

## `.env` 檔案

`unified_io/.env` 是 SQL adapter 連線字串等機密設定的預留位置，**不應版控**（已在 `.gitignore` 中）。

---

開發/架構細節（含每個檔案目前的實作狀態）請見 [agent.md](agent.md)。
