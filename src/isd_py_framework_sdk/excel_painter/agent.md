# agent.md — `excel_painter` 套件

## 狀態：新建可用（2026-06）

全新乾淨子套件，取代先前作為參考拉進來的 `BetterPyExcelHelper`（已退役）。設計來源：整併 `BetterPyExcelHelper` 與 `NTUAddressRefilligGUI` / `SecondOrgRefillingForGivenAuthor` 兩專案的所有 Excel 上色／排版做法。

驗證（src 在 path 上）：

```powershell
$env:PYTHONPATH="src"; .venv\Scripts\python.exe -c "from isd_py_framework_sdk.excel_painter import ExcelPainter, save_styled_table, SheetFormatSnapshot, STATUS_GREEN, display_width; print(display_width('台大ABC'))"
```

---

## 職責

把 openpyxl 的樣式操作包成「load 一次 → 鏈式套用 → save 一次」的 `ExcelPainter`，並提供宣告式 `TableStyle`、條件填色、CJK 自動欄寬、格式快照、文字差異上色。

### 與 unified_io 的雙向聯通

`unified_io` 的 Excel adapter 在兩處委派本套件（連通點僅此）：
- `mode="preserve"` → `SheetFormatSnapshot`（`from ...excel_painter import SheetFormatSnapshot`）
- `mode="styled"` / 傳 `style=` → `save_styled_table`

分工：`unified_io` 管資料搬運（格式不可知），`excel_painter` 管呈現。本套件**不**反向 import `unified_io`（避免循環）。範例：`examples/excel_painter/io_integration.py`。

---

## 架構

```
excel_painter/
├── __init__.py          flat 匯出全部公開 API
├── painter.py           ExcelPainter（fluent 核心，每個方法回傳 self）
├── templates.py         函式化的專業報表模板（status_report / summary_statistics_report / multi_sheet_report / diff_highlight_report + auto_status_fills）
├── convenience.py       save_styled_table / style_existing（函式便利層）
├── styles.py            TableStyle、fill/font/box/side/align、STATUS_* 常數、預設變體
├── width.py             display_width（wcwidth 選用 + unicodedata fallback）、auto_resize
├── highlight.py         char_lcs/word_lcs/common_words + *_rich_text（CellRichText 產生器，pure）
└── _format_snapshot.py  SheetFormatSnapshot.capture/restore
```

分層原則：`highlight.py`、`width.py`、`_format_snapshot.py`、`styles.py` 皆為**純函式/資料**（不持有 workbook）；`painter.py` 是唯一持有 `wb`/`ws` 狀態的地方；`convenience.py` 只是 painter 的 thin 包裝。

---

## 設計決策（為何這樣寫）

- **stays-open 物件 vs 程序式**：舊 helper 每個操作 `load_workbook`+`save` 重開檔，鏈式極慢。`ExcelPainter` 持有 workbook，方法回傳 `self`。
- **欄位參數同時吃欄名與 1-based 索引**：`_col(col, header_row)` 統一解析。專案實戰大量用「依 header 名給寬度/wrap」，但底層上色又用索引，故兩者都支援。
- **狀態色彩 = `(底色, 字色)` tuple**：兩專案都用 `回填狀態 → (bg, font)` 的對映；`fill_by_value` 直接吃這格式（也接受純底色字串）。
- **CJK 寬度 fallback**：`wcwidth` 為選用 extra；無安裝時以 `unicodedata.east_asian_width` 內建計算，符合 SDK「預設不裝重依賴」哲學。
- **`save(safe=True)`**：複製 `report_builder` 的「檔案被 Excel 鎖住 → 改存時間戳副本」行為，避免 `PermissionError` 中斷流程。
- **rich-text 產生器為 pure**：`*_rich_text()` 回傳 `CellRichText`，不碰 workbook；painter 的 `highlight_*()` 負責寫回儲存格。

---

## 常見陷阱

- **`openpyxl` 為必要依賴**；`wcwidth` 為選用。import `excel_painter` 時即需要 openpyxl。
- `style_table()` 的 `widths` 只設「有給」的欄；要全欄自動寬請先 `auto_width()`。`save_styled_table(auto_width=True)` 的順序是先 auto_width 再套 `widths`（明確寬度覆蓋自動）。
- `SheetFormatSnapshot` **不保留** `CellRichText`（重寫值時只還原 cell *style*）、charts/images/data-validation/conditional-formatting。
- `freeze(row=1)` 代表「凍結第 1 列以上」→ `freeze_panes="A2"`（與 openpyxl 慣例一致：傳入的是「第一個可捲動的儲存格」的前一格）。
- **尚無 pytest 測試檔**；建議補 `tests/excel_painter/`（style_table 落地、fill_by_value、snapshot/restore roundtrip、CJK width）。

---

## 來源做法對照（整併自哪裡）

| 能力 | 整併來源 |
|---|---|
| 表頭色帶＋框線＋凍結＋autofilter＋number_format | `SecondOrg/src/engine.py::_style_table`、`review_app._write_final_excel` |
| 狀態色彩對映 | 兩專案的 `_STATUS_FILL` |
| 單格寫入原語 / block 框線 | `NTU/.../build_analysis_xlsx.py::wc` |
| 檔案鎖 fallback | `NTU/.../report_builder.py::_save_report_xlsx` |
| CJK 自動欄寬、隱藏欄、凍結、一條龍存檔 | `BetterPyExcelHelper/view_helper.py` |
| LCS / Jaccard 逐字逐詞上色 | `BetterPyExcelHelper/excel_painter.py` |
| 格式快照 | 為 `unified_io` 的 `preserve` 模式新設計 |

> 注意：`app/excel_compat.py`（calamine 讀取相容層，繞過 Py3.14 openpyxl read-only 串流崩潰）屬「讀取」議題，不在本上色套件範圍；若 SDK 要支援 Py3.14 大檔讀取，應放在 `unified_io` 的 Excel reader。

## 未整併（刻意排除）

`BetterPyExcelHelper` 的純 DataFrame 工具（`multiple_sort_dataframe`、`pick_and_reorder_then_rename_columns`、`dict_to_df`、`get_value_from_cell`、欄字母↔數字）**不屬於 painter 範圍**，未移植。欄字母↔數字 openpyxl 已內建（`get_column_letter` / `column_index_from_string`）。其餘 df 工具若仍需要，應另開 df-helpers 模組或併入 `unified_io`。
