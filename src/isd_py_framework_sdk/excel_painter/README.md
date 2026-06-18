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

## 依賴

```bash
pip install isd-py-framework-sdk[excel_painter]   # openpyxl + wcwidth
```

`openpyxl` 為必要；`wcwidth` 為選用（沒有時 `display_width` 以 `unicodedata` 內建 fallback 計算 CJK 寬度）。

---

開發／架構細節見 [agent.md](agent.md)。
