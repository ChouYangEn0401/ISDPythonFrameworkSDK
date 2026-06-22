# agent.md — `unified_io` 套件

## 目前狀態：已實作可用（2026-06 重新驗證，io_module 合併後）

整個套件可正常 import 並完成 round-trip。先前版本的 agent.md 描述的「空檔案 stub」狀態**已過時**——所有 adapter 皆已實作。

| 檔案 | 狀態 |
|---|---|
| `data_io.py` | ✅ `DataIO` façade（auto 格式判斷 + 各格式便利方法）|
| `adapters/_interface.py` | ✅ `IReader` / `IWriter` / `IIOAdapter`（ABC）|
| `adapters/csv_adapter.py` | ✅ `CsvIOAdapter` |
| `adapters/excel_adapter.py` | ✅ `ExcelIOAdapter`（`fresh` / `inplace` / `preserve` 皆可用）|
| `adapters/json_adapter.py` | ✅ `JsonIOAdapter`（JSON + JSONL）|
| `adapters/sql_adapter.py` | ✅ `SqlIOAdapter` |
| `legacy.sql_writer.py` | ⚠️ 舊版獨立 Tkinter 上傳腳本，非套件 API，可考慮刪除 |

驗證指令（src 在 path 上）：

```powershell
$env:PYTHONPATH="src"; .venv\Scripts\python.exe -c "from isd_py_framework_sdk.unified_io import DataIO; import pandas as pd; DataIO.write(pd.DataFrame({'a':[1]}), 't.csv'); print(DataIO.read('t.csv').shape)"
```

---

## 職責

提供統一的資料 IO 介面，讓上層業務邏輯不需關心底層格式（CSV、Excel、JSON/JSONL、SQL），一律以 `pandas.DataFrame` 作為中間格式。

`unified_io` 與 `file_compare` **不重疊**：前者負責讀寫資料，後者是 unittest 用的檔案內容比對（`compare_*_files`）。專案中目前沒有其他通用資料 IO 模組，因此本套件並非冗餘。

> 根層 `__init__.py` 不 re-export `unified_io`；請以完整路徑 `from isd_py_framework_sdk.unified_io import ...` 匯入（CLAUDE.md 快速導覽表亦如此標示）。

---

## 架構

```
unified_io/
├── __init__.py          匯出 DataIO, 四個 Adapter, 三個介面
├── data_io.py           DataIO façade（_resolve_adapter 依副檔名選 adapter）
├── .env                 SQL 連線機密（不版控）
├── legacy.sql_writer.py 舊版 Tkinter 腳本（非 API）
└── adapters/
    ├── __init__.py      匯出 CsvIOAdapter, ExcelIOAdapter, JsonIOAdapter, SqlIOAdapter
    ├── _interface.py    IReader, IWriter, IIOAdapter（ABC）
    ├── csv_adapter.py
    ├── excel_adapter.py
    ├── json_adapter.py
    └── sql_adapter.py
```

`DataIO.read/write` 流程：`format="auto"` 時依 `Path(source).suffix` 對照 `_EXT_MAP` 選擇 adapter；帶 `engine=` 或 `format="sql"` 時走 `SqlIOAdapter`。

---

## 核心介面

```python
from isd_py_framework_sdk.unified_io import IReader, IWriter, IIOAdapter

class IReader(ABC):
    def read(self, source, **kwargs) -> pd.DataFrame: ...

class IWriter(ABC):
    def write(self, df, destination, **kwargs) -> None: ...

class IIOAdapter(IReader, IWriter, ABC): ...
```

所有 adapter 皆以 `pd.DataFrame` 為中間格式。

---

## 具體 Adapter

| Adapter | 讀 | 寫 | extras | 備註 |
|---|---|---|---|---|
| `CsvIOAdapter` | `pd.read_csv` | `to_csv`（`index=False`）| `[unified_io]` | |
| `ExcelIOAdapter` | `pd.read_excel` | 見下方寫入模式 | `[unified_io.excel]` | import 時檢查 openpyxl |
| `JsonIOAdapter` | `pd.read_json` | `to_json`（`orient="records"`）| `[unified_io]` | `lines=True` → JSONL |
| `SqlIOAdapter` | `pd.read_sql` | `to_sql`（`if_exists="append"`）| `[unified_io.sql]` | engine 可由 constructor 或 `engine=` 傳入 |

### Excel 寫入模式

- `"fresh"`（預設）：`to_excel` 整張重寫，最快，不保留格式。
- `"inplace"`：開既有 workbook 只改資料範圍儲存格值，保留其餘格式（含範圍外 CellRichText）。欄數需與既有 sheet 相符。**自包含、可用**。
- `"preserve"`：擷取格式快照→重寫→還原。**已可用**——`_write_preserve` 透過 `isd_py_framework_sdk.excel_painter.SheetFormatSnapshot` 保留 fills/字型/欄寬/凍結/合併，只刷新儲存格值。檔案不存在時 fallback 到 `fresh`；sheet 不存在時以 append 寫新分頁。
- `"styled"`（或在 `write()` 傳 `style=`）：`_write_styled` 委派給 `excel_painter.save_styled_table`，邊寫邊套用表格樣式（表頭色帶/框線/凍結/autofilter/欄寬/wrap/狀態色碼）。`style` 接受 `TableStyle` 或 `True`（預設外觀）；其餘 styling 選項（`widths`/`wrap_cols`/`text_cols`/`status_column`/`status_fills`/`auto_width`…）由 `**kwargs` 直通。

### 與 excel_painter 的聯通（架構分工）

`unified_io` = 資料搬運（DataFrame in/out，格式不可知）；`excel_painter` = 呈現（排版上色）。連通點只在 Excel adapter：
- `preserve` → `excel_painter.SheetFormatSnapshot.capture/restore`
- `styled` / `style=` → `excel_painter.save_styled_table`

其餘 adapter（CSV/JSON/SQL）與 `excel_painter` 無關，維持輕量。範例：`examples/excel_painter/io_integration.py`。

---

## 已知注意事項 / 待辦

- **`preserve` 模式依賴 `excel_painter.SheetFormatSnapshot`**（同 repo 的 sibling 子套件，已實作）。需要 `[unified_io.excel]` 或 `[excel_painter]` extra（openpyxl）。
- **沒有 pytest 測試檔**。建議在 `tests/` 補上 round-trip 測試（CSV/JSON/JSONL/Excel-fresh/inplace/preserve）。
- `pandas` 是所有 adapter 的必要依賴；openpyxl / sqlalchemy 在對應 adapter 內 lazy 檢查並給出安裝提示。
- `legacy.sql_writer.py` 為舊腳本（含 Tkinter GUI、硬編 batch 邏輯），非套件 API，可移除以減少混淆。
- `.env` 含真實 MSSQL 連線憑證；已於 `.gitignore` 以 `**/.env` 排除——切勿提交。

---

## 擴充新格式

1. 在 `adapters/` 新增 `<format>_adapter.py`，繼承 `IIOAdapter` 實作 `read()` / `write()`。
2. 在 `adapters/__init__.py` 與 `unified_io/__init__.py` 匯出。
3. 在 `data_io.py` 的 `_EXT_MAP` 註冊副檔名（若需 auto 判斷）。
4. 有外部依賴時於 `pyproject.toml` 新增 extras。
