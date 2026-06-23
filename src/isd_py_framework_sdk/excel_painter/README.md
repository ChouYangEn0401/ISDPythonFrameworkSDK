# `excel_painter` — 強大的 Excel 樣式工具

把多個專案散落的 Excel 上色／排版做法，收斂成一個乾淨、可鏈式呼叫的工具。

## 設計核心：load 一次 → 鏈式套用 → save 一次

舊版 helper 每個操作都重開／重存檔，鏈式操作極慢。`ExcelPainter` 把 workbook 留在記憶體，每個方法回傳 `self`：

```python
from isd_py_framework_sdk.excel_painter import ExcelPainter, STATUS_GREEN, STATUS_RED

(
    ExcelPainter.from_dataframe(df, sheet_name="Results")
    .style_table(widths={"Name": 22, "說明": 80}, wrap_cols=["說明"], text_cols=["ISI_ID"])
    .fill_by_value("狀態", {"✅完成": STATUS_GREEN, "❌失敗": STATUS_RED})
    .auto_width(only_columns=[1])
    .save("out.xlsx", safe=True)
)
```

欄位參數一律可用**欄名**或 **1-based 整數索引**（依 `header_row` 解析）。

## 一行搞定（函式便利層）

```python
from isd_py_framework_sdk.excel_painter import save_styled_table, STATUS_GREEN

save_styled_table(
    df, "out.xlsx",
    widths={"Name": 22}, wrap_cols=["說明"], text_cols=["ISI_ID"],
    status_column="狀態", status_fills={"✅完成": STATUS_GREEN},
    auto_width=True, safe=True,
)
```

`style_existing(path, ...)` 則是開啟既有檔 → 套樣式 → 存回。

## 專業報表模板（一行產出）

常見報表已函式化（`templates.py`），不必自己組鏈：

```python
from isd_py_framework_sdk.excel_painter import (
    status_report, summary_statistics_report, multi_sheet_report, diff_highlight_report,
)

# 1) 狀態色碼結果表（+ 自動統計摘要分頁；status_fills 省略時自動依 ✅/⚠/❌ 推斷）
status_report(df, "out.xlsx", status_column="回填狀態", title="NA 回填結果",
              wrap_cols=["AI說明"], text_cols=["ISI_ID"])

# 2) 數值統計表（數值欄熱力圖漸層 + 總計列）
summary_statistics_report(df, "out.xlsx", numeric_cols=["2023", "2024"], label_col="系所")

# 3) 多分頁活頁簿（每頁套表格樣式 + 自動「總覽」索引頁）
multi_sheet_report({"已解決": df1, "未解決": df2}, "out.xlsx")

# 4) 逐列詞彙差異高亮（LCS / 共同詞）
diff_highlight_report(df, "out.xlsx", column_pairs=[("原始地址", "比中地址")])
```

範例藝廊：`examples/excel_painter/generate_templates.py` 會在 `examples/excel_painter/output/` 產出 5 個專業範例檔，可直接開來看效果。

## 能力一覽

| 類別 | 方法 / 物件 |
|---|---|
| **表格樣式器**（核心）| `style_table()`：表頭色帶＋框線＋欄寬＋wrap/align＋凍結表頭＋autofilter＋`@` 文字格式 |
| **條件／狀態填色** | `fill_by_value(col, {值: (底色,字色)})`、`fill_where(col, predicate, color)`、`fill_cell()` |
| **CJK 自動欄寬** | `auto_width()` / `display_width()`（優先用 `wcwidth`，無則內建 East-Asian 寬度 fallback）|
| **格式快照** | `snapshot()` / `restore()`、`SheetFormatSnapshot`（`unified_io` 的 `preserve` 寫入即用此）|
| **文字差異上色** | `highlight_lcs()`、`highlight_common_words()`（回傳 `CellRichText`，逐字／逐詞上色）|
| **結構** | `freeze()`、`hide_columns()`、`add_autofilter()`、`number_format()`、`set_widths()` |
| **區域迭代** | `for_each(axis, callback, fixed=...)` |
| **安全存檔** | `save(path, safe=True)`：檔案被 Excel 鎖住時自動改存時間戳副本；`open_after=True` 存後開檔 |

### 樣式預設

`TableStyle` 為宣告式樣式（深藍表頭＋白粗體＋thin 灰框線＋凍結＋autofilter 為預設）。提供 `blue_table()` 與 `minimal_table()` 兩個現成變體，也可自行調整欄位（`banded=True` 開斑馬紋等）。

狀態色彩常數：`STATUS_GREEN` / `STATUS_AMBER` / `STATUS_RED` / `STATUS_GREY`，皆為 `(底色, 字色)` tuple。

## 與 `unified_io` 的整合

`unified_io`（資料 IO 層）可直接委派給本套件做排版：

```python
from isd_py_framework_sdk.unified_io import DataIO
DataIO.write(df, "report.xlsx", style=True, widths={"Name": 20}, status_column="狀態", ...)
```

- `DataIO.write(..., style=...)` / `mode="styled"` → 委派 `save_styled_table`
- `DataIO.write(..., mode="preserve")` → 使用本套件的 `SheetFormatSnapshot`

範例：`examples/excel_painter/io_integration.py`。

## 依賴

```bash
pip install isd-py-framework-sdk[excel_painter]   # openpyxl + wcwidth
```

`openpyxl` 為必要；`wcwidth` 為選用（沒有時 `display_width` 以 `unicodedata` 內建 fallback 計算 CJK 寬度）。

---

開發／架構細節見 [agent.md](agent.md)。
