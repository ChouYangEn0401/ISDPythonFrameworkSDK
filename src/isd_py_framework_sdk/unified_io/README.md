# `unified_io` — 統一資料 IO 介面

## 狀態：已實作可用（2026-06 重新驗證）

透過 adapter 模式，提供統一的資料讀寫介面，讓上層業務邏輯不需關心底層格式（CSV、Excel、JSON/JSONL、SQL），一律以 `pandas.DataFrame` 為中間格式。

`DataIO` façade、四個 adapter（CSV / Excel / JSON / SQL）與介面（`IReader` / `IWriter` / `IIOAdapter`）皆已實作並通過 round-trip 驗證。

> **與 `file_compare` 的差異**：`file_compare` 是 unittest 用的「檔案內容比對」工具（`compare_*_files`），目的是驗證輸出是否符合預期；`unified_io` 是「資料讀寫」工具。兩者用途不同、不重疊。

## 快速開始

```python
from isd_py_framework_sdk.unified_io import DataIO

# ── 讀取（format 預設 "auto"，依副檔名判斷）──────────────────
df = DataIO.read("data.csv")
df = DataIO.read("report.xlsx", sheet_name="Sales")
df = DataIO.read("data.jsonl", format="jsonl")
df = DataIO.read_sql("SELECT * FROM orders", engine=engine)

# ── 寫入 ─────────────────────────────────────────────────────
DataIO.write(df, "output.csv")
DataIO.write(df, "output.xlsx", sheet_name="Summary")
DataIO.write(df, "report.xlsx", mode="inplace")   # 只改值、保留版面
```

也可直接使用 adapter 取得 constructor 層級的選項：

```python
from isd_py_framework_sdk.unified_io import ExcelIOAdapter

adapter = ExcelIOAdapter(default_write_mode="inplace")
df = adapter.read("report.xlsx", sheet_name="Data")
adapter.write(df_updated, "report.xlsx", sheet_name="Data")
```

## 具體 Adapter

| Adapter | 讀來源 | 寫目標 | 需要 extras |
|---|---|---|---|
| `CsvIOAdapter` | CSV 路徑 | CSV 路徑 | `[unified_io]`（pandas）|
| `ExcelIOAdapter` | xlsx 路徑 | xlsx 路徑 | `[unified_io.excel]`（pandas + openpyxl）|
| `JsonIOAdapter` | JSON/JSONL 路徑 | JSON/JSONL 路徑 | `[unified_io]`（pandas）|
| `SqlIOAdapter` | SQL query / table | table name | `[unified_io.sql]`（pandas + sqlalchemy）|

### Excel 寫入模式（`mode=`）

| 模式 | 行為 | 備註 |
|---|---|---|
| `"fresh"`（預設）| `to_excel` 重寫整張 sheet | 最快，**不保留**既有格式 |
| `"inplace"` | 只更新資料範圍的儲存格值 | 保留其餘格式；DataFrame 欄數需與既有 sheet 相符 |
| `"preserve"` | 擷取格式快照→重寫→還原 | 透過 `excel_painter.SheetFormatSnapshot` 保留 fills/字型/欄寬/凍結/合併；只刷新值、保留手工版面 |
| `"styled"`（或傳 `style=`）| 透過 `excel_painter.save_styled_table` 邊寫邊排版 | 表頭色帶＋框線＋凍結＋autofilter＋欄寬/wrap＋狀態色碼，一步到位 |

### 與 `excel_painter` 的聯通

IO 層負責「資料搬運」，`excel_painter` 負責「呈現」。兩者透過 Excel adapter 連通：

```python
from isd_py_framework_sdk.unified_io import DataIO
from isd_py_framework_sdk.excel_painter import STATUS_GREEN, STATUS_RED

# 直接用 IO 介面輸出「專業排版」的 Excel（內部委派給 excel_painter）
DataIO.write(
    df, "report.xlsx",
    style=True,                                   # 啟用排版（也可傳 TableStyle）
    widths={"Name": 20}, wrap_cols=["說明"], text_cols=["ISI_ID"],
    status_column="狀態", status_fills={"✅完成": STATUS_GREEN, "❌失敗": STATUS_RED},
)
```

`mode="preserve"` 同樣依賴 `excel_painter` 的 `SheetFormatSnapshot`。範例見 `examples/excel_painter/io_integration.py`。

## 依賴 Extras

```bash
pip install isd-py-framework-sdk[unified_io]          # 核心：CSV + JSON
pip install isd-py-framework-sdk[unified_io.excel]    # + Excel
pip install isd-py-framework-sdk[unified_io.sql]      # + SQL
```

## `.env` 檔案

`unified_io/.env` 用於存放 SQL adapter 的連線字串等機密設定，**不應版控**（已於 `.gitignore` 以 `**/.env` 排除）。請勿提交真實憑證。

---

開發/架構細節與每個檔案的實作狀態請見 [agent.md](agent.md)。
