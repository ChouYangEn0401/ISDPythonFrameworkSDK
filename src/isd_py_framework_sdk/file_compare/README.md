# `file_compare` — 多格式檔案比對工具

快速比對「待測輸出」與「預期標準」，主要用於輔助 unittest/pytest 驗證輸出檔案是否與基準檔（baseline）一致。支援 9 種檔案格式，共享統一的 Config 介面與 **Masking** 機制。

## 支援格式

| 格式 | 子模組 | 函式 | 額外套件 |
|---|---|---|---|
| Excel (.xlsx) | `excel_unittest_module` | `compare_excel_sheets` | `openpyxl` |
| CSV | `csv_unittest_module` | `compare_csv_files` | — |
| JSON | `json_unittest_module` | `compare_json_files` | — |
| JSONL | `jsonl_unittest_module` | `compare_jsonl_files` | — |
| TXT | `txt_unittest_module` | `compare_txt_files` | — |
| YAML | `yaml_unittest_module` | `compare_yaml_files` | `pyyaml` |
| XML | `xml_unittest_module` | `compare_xml_files` | — |
| INI | `ini_unittest_module` | `compare_ini_files` | — |
| TOML | `toml_unittest_module` | `compare_toml_files` | — (Python 3.11+) |

## Import 方式

三種 import 方式均支援（以 TOML 為例，其餘格式同理）：

```python
# 方式 1：從子模組精準匯入
from isd_py_framework_sdk.file_compare.toml_unittest_module import compare_toml_files

# 方式 2：子模組別名
import isd_py_framework_sdk.file_compare.toml_unittest_module as m
m.compare_toml_files(...)

# 方式 3：從 file_compare 頂層平舖匯入（推薦）
from isd_py_framework_sdk.file_compare import compare_toml_files
```

## 安裝

```bash
# 安裝核心（無 heavy 後端）
pip install isd-py-framework-sdk

# 安裝 Excel 後端
pip install isd-py-framework-sdk["file_compare.excel"]

# 安裝 YAML 後端
pip install isd-py-framework-sdk["file_compare.yaml"]

# 安裝所有 file_compare 後端（Excel + YAML）
pip install isd-py-framework-sdk[file_compare]

# 安裝開發工具與所有後端
pip install isd-py-framework-sdk[all]
```

> 由於 `__init__.py` 採用 lazy import，未安裝的後端只在**實際呼叫**對應函式時才會 `ImportError`，不會影響其他格式的使用。

---

## Masking 機制

所有模組支援 `mask` 參數，可精準指定要比對或跳過的範圍。

### 行式格式（Excel / CSV / TXT / JSONL）

```python
"mask": {
    "include_rows": [1, 2, 3],   # 只比對這些行（1-indexed）
    "exclude_rows": [5, 10],     # 跳過這些行
    # ----- 以下僅 Excel 和 CSV 支援 -----
    "include_cols": ["A", "B"],  # 只比對這些欄（Excel 用字母；CSV 用 0-indexed int）
    "exclude_cols": ["C"],       # 跳過這些欄
    "exclude_cells": ["A1"],     # 跳過特定儲存格（僅 Excel）
}
```

> `include_rows` 和 `exclude_rows` 可同時使用：先取 include 範圍，再減去 exclude。

### 樹狀格式（JSON / YAML / TOML）

```python
"mask": {
    "include_paths": ["$.data", "$.config"],      # 只比對這些路徑
    "exclude_paths": ["$.metadata.timestamp"],     # 跳過這些路徑
}
```

路徑格式：`$` 為根，用 `.` 分隔 key，用 `[i]` 索引 list 元素。

### XML

```python
"mask": {
    "exclude_tags": ["timestamp", "generated"],    # 跳過含有這些 tag 的元素
}
```

### INI

```python
"mask": {
    "include_sections": ["database", "server"],    # 只比對這些區段
    "exclude_sections": ["debug"],                 # 跳過這些區段
    "exclude_keys": {"server": ["timestamp"]},     # 跳過特定區段中的特定 key
}
```

---

## 快速範例

### Excel

```python
from isd_py_framework_sdk.file_compare import compare_excel_sheets

compare_excel_sheets({
    "target_path": "output.xlsx",
    "bench_path":  "expected.xlsx",
    "sheets": [
        {
            "target_sheet": "Result",
            "bench_sheet":  "Result",
            "checks": ["content", "color", "type", "freeze", "hidden"],
            "mask": {
                "exclude_rows": [1],         # 跳過標題行
                "exclude_cols": ["A"],        # 跳過 A 欄
                "exclude_cells": ["B2"],      # 跳過 B2 儲存格
            },
            # 向下相容：skip 可與 mask 並用
            "skip": {
                "correct": ["C3"],            # 預期改動的儲存格
                "false":   ["D4"],            # 已知錯誤的儲存格
            },
        },
    ],
})
```

支援的 `checks`：`content`、`color`、`type`、`freeze`、`hidden`。

### CSV

```python
from isd_py_framework_sdk.file_compare import compare_csv_files

compare_csv_files({
    "target_path": "output.csv",
    "bench_path":  "expected.csv",
    "encoding":    "utf-8",       # 選填，預設 utf-8
    "delimiter":   ",",           # 選填，預設 ","
    "checks":      ["content", "row_count", "column_count", "header"],
    "mask":        {"exclude_rows": [1]},
})
```

### JSON

```python
from isd_py_framework_sdk.file_compare import compare_json_files

compare_json_files({
    "target_path": "output.json",
    "bench_path":  "expected.json",
    "mask": {"exclude_paths": ["$.metadata.timestamp"]},
})
```

### JSONL

```python
from isd_py_framework_sdk.file_compare import compare_jsonl_files

compare_jsonl_files({
    "target_path": "output.jsonl",
    "bench_path":  "expected.jsonl",
    "mask": {"include_rows": [1, 3, 5]},
})
```

### TXT

```python
from isd_py_framework_sdk.file_compare import compare_txt_files

compare_txt_files({
    "target_path": "output.txt",
    "bench_path":  "expected.txt",
    "strip":  True,                        # 選填，去除首尾空白再比對
    "case":   "upper",                     # 選填: "upper" | "lower"，比對前統一大小寫
    "checks": ["content", "line_count"],
    "mask":   {"exclude_rows": [1, 2]},
})
```

### YAML

```python
from isd_py_framework_sdk.file_compare import compare_yaml_files

compare_yaml_files({
    "target_path": "output.yaml",
    "bench_path":  "expected.yaml",
    "mask": {"exclude_paths": ["$.generated_at"]},
})
```

### XML

```python
from isd_py_framework_sdk.file_compare import compare_xml_files

compare_xml_files({
    "target_path": "output.xml",
    "bench_path":  "expected.xml",
    "checks": ["tag", "text", "attrib", "children_count"],
    "mask":   {"exclude_tags": ["timestamp"]},
})
```

### INI

```python
from isd_py_framework_sdk.file_compare import compare_ini_files

compare_ini_files({
    "target_path": "output.ini",
    "bench_path":  "expected.ini",
    "mask": {
        "exclude_sections": ["debug"],
        "exclude_keys":     {"server": ["timestamp"]},
    },
})
```

### TOML

```python
from isd_py_framework_sdk.file_compare import compare_toml_files

compare_toml_files({
    "target_path": "output.toml",
    "bench_path":  "expected.toml",
    "mask": {"exclude_paths": ["$.metadata.generated_at"]},
})
```

---

## 測試

```powershell
# 執行所有格式的比對測試
.venv\Scripts\python.exe -m pytest -v tests/test_file/

# 執行單一格式
.venv\Scripts\python.exe -m pytest -v tests/test_file/test_json.py
.venv\Scripts\python.exe -m pytest -v tests/test_file/test_excel.py   # 需 [file_compare.excel]
.venv\Scripts\python.exe -m pytest -v tests/test_file/test_yaml.py    # 需 [file_compare.yaml]

# 重新產生測試樣本
.venv\Scripts\python.exe tests/test_file/generate_samples.py
```

---

開發/架構細節（lazy import 設計、擴充新格式步驟）請見 [agent.md](agent.md)。
