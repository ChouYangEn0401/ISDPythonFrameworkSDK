tests/test_file — 快速指南
==========================

本資料夾提供兩種用途：
1. **產生 sample 檔案**（`generate_samples.py`）供比對工具使用
2. **現成的測試腳本**（`test_*.py` / `run_all.py`），安裝 wheel 後即可直接執行

---

## 一、產生 base sample 檔案

```bash
python tests/test_file/generate_samples.py
```

會在 `tests/test_file/base/` 下建立以下格式的 sample 與 [BU] backup 對：

| 格式  | 待測檔（target）     | 標準備份（bench）         |
|-------|----------------------|---------------------------|
| csv   | sample.csv           | [BU] sample.csv           |
| xlsx  | sample.xlsx          | [BU] sample.xlsx          |
| jsonl | sample.jsonl         | [BU] sample.jsonl         |
| txt   | sample.txt           | [BU] sample.txt           |

---

## 二、執行 sample 測試（安裝 wheel 之後）

### 依格式分開執行

```bash
python tests/test_file/test_csv.py
python tests/test_file/test_excel.py
python tests/test_file/test_jsonl.py
python tests/test_file/test_txt.py
```

### 一次執行全部

```bash
python tests/test_file/run_all.py
```

若所有測試通過，會印出 `All tests PASSED.` 並以 exit code 0 結束；
任一失敗則以 exit code 1 結束。

---

## 三、各格式支援的 checks / mask

### CSV (`compare_csv_files`)

| `checks` 選項 | 說明 |
|---|---|
| `content`      | 逐行逐欄比對儲存格值 |
| `row_count`    | 比對總行數 |
| `column_count` | 比對第一行的欄數 |
| `header`       | 比對標題行 |

**mask** 支援 `include_rows`、`exclude_rows`（1-indexed）、`include_cols`、`exclude_cols`（0-indexed）。

### Excel (`compare_excel_sheets`)

| `checks` 選項 | 說明 |
|---|---|
| `content` | 逐儲存格比對值 |
| `color`   | 比對填充色（openpyxl `start_color.rgb`） |
| `freeze`  | 比對凍結範圍（freeze_panes） |
| `hidden`  | 比對欄位隱藏狀態 |

**mask** 支援 `include_rows`、`exclude_rows`、`include_cols`、`exclude_cols`（均為 Excel 欄位字母）、`exclude_cells`（單格如 `"A1"`）。

也支援 **skip**：`correct`（預期改動）與 `false`（已知假錯誤）。

### JSONL (`compare_jsonl_files`)

逐行解析 JSON 並做深度遞迴比對（dict / list / scalar）。

**mask** 支援 `include_rows`、`exclude_rows`（1-indexed）。

### TXT (`compare_txt_files`)

| `checks` 選項 | 說明 |
|---|---|
| `content`    | 逐行比對文字 |
| `line_count` | 比對總行數 |

可設 `strip: true` 去除首尾空白後再比對。

**mask** 支援 `include_rows`、`exclude_rows`（1-indexed）。

---

## 四、自訂測試（以 excel 為例）

複製 `test_excel.py`，修改 `target_path`、`bench_path` 與 `sheets` 設定即可套用到你自己的專案檔案。