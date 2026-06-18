# agent.md — `file_compare` 套件

## 職責

提供多格式檔案比對工具，主要用途是輔助 unittest/pytest，快速驗證程式的輸出檔案是否與預期的基準檔（baseline）一致。支援 CSV、Excel、INI、JSON、JSONL、TOML、TXT、XML、YAML 九種格式。

---

## 架構

```
file_compare/
├── __init__.py                    公開 API（lazy import 包裝）
├── _shared.py                     共用色彩常數 & 比對輔助函式
├── html_report.py                 產生 HTML 比對報告
├── csv_unittest_module/
│   ├── __init__.py
│   └── run_csv_structure_test.py   compare_csv_files() 實作
├── excel_unittest_module/
│   ├── __init__.py
│   └── run_excel_structure_test.py  compare_excel_sheets() 實作
├── ini_unittest_module/           compare_ini_files()
├── json_unittest_module/          compare_json_files()
├── jsonl_unittest_module/         compare_jsonl_files()
├── toml_unittest_module/          compare_toml_files()（Python 3.11+ tomllib）
├── txt_unittest_module/           compare_txt_files()
├── xml_unittest_module/           compare_xml_files()
└── yaml_unittest_module/          compare_yaml_files()（需 pyyaml）
```

---

## Lazy Import 設計

`__init__.py` 以 `importlib.import_module` 實作延遲載入，確保：
1. `from isd_py_framework_sdk.file_compare import compare_toml_files` 在 import 時不會觸發 TOML backend 的載入
2. 只有**實際呼叫**對應函式時才 import 子模組
3. 未安裝對應 extras（如 `pyyaml`、`openpyxl`）時，只在呼叫相關函式時才 `ImportError`，而不影響其他格式

```python
def _lazy_attr(module_name: str, attr: str) -> Any:
    mod = import_module(f".{module_name}", __package__)
    return getattr(mod, attr)

def compare_yaml_files(*args, **kwargs):
    return _lazy_attr("yaml_unittest_module", "compare_yaml_files")(*args, **kwargs)
```

---

## 依賴 Extras

| 格式 | 需要安裝 |
|---|---|
| CSV | 無（標準庫） |
| JSON / JSONL / TXT / XML | 無（標準庫） |
| TOML | 無（Python 3.11+ 內建 `tomllib`） |
| INI | 無（標準庫 `configparser`） |
| YAML | `pip install isd-py-framework-sdk["file_compare.yaml"]`（pyyaml）|
| Excel | `pip install isd-py-framework-sdk["file_compare.excel"]`（openpyxl + pandas）|
| 全部 | `pip install isd-py-framework-sdk[file_compare]` |

---

## 公開 API

```python
from isd_py_framework_sdk.file_compare import (
    compare_csv_files,
    compare_excel_sheets,
    compare_ini_files,
    compare_json_files,
    compare_jsonl_files,
    compare_toml_files,
    compare_txt_files,
    compare_xml_files,
    compare_yaml_files,
)
```

每個函式接受兩個路徑（`actual`, `expected`）並在差異時拋出 AssertionError 或印出差異報告（依各模組實作而定）。

---

## Masking 機制（`mask` 參數）

所有比對函式接受可選的 `mask` config，用來縮小比對範圍。實作集中在 `_shared.py`：

- `resolve_row_mask()` — 行式格式共用（Excel/CSV/TXT/JSONL）：`include_rows` / `exclude_rows`（1-indexed），Excel/CSV 額外支援 `include_cols` / `exclude_cols` / `exclude_cells`。
- `deep_compare()` 的 `exclude_paths` / `include_paths` 參數 — 樹狀格式（JSON/YAML/TOML）用 `$.foo.bar` / `$.arr[i]` 路徑語法做前綴比對。
- XML 用 `exclude_tags`；INI 用 `include_sections` / `exclude_sections` / `exclude_keys`（各模組自行實作，不在 `_shared.py`）。

完整使用範例見 [README.md](README.md)。

---

## 測試檔案結構

```
tests/test_file/
├── base/                         基準（預期）檔案
│   ├── sample.csv / [BU] sample.csv
│   ├── sample.json / [BU] sample.json
│   └── ...（各格式 × 2）
├── generate_samples.py           產生測試樣本的腳本
├── test_csv.py / test_json.py / ...
└── README.md
```

`[BU]` 前綴是「備份」（Backup）版本，可作為基準比對。

---

## 進入點與測試

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

## 擴充新格式

1. 在 `file_compare/` 下新增 `<format>_unittest_module/` 目錄
2. 實作 `run_<format>_structure_test.py`（含 `compare_<format>_files` 函式）
3. 在 `__init__.py` 加入 lazy wrapper 函式
4. 若有外部依賴，在 `pyproject.toml` 加入對應 extras

---

## 常見陷阱

- Excel 比對（`compare_excel_sheets`）依賴 `openpyxl` 和 `pandas`；未安裝時呼叫會 `ImportError`，而不是 import 時就失敗。
- TOML 格式需要 Python 3.11+（使用標準庫 `tomllib`）。
- 各格式的比對細節（欄位順序、空白處理、浮點精度）在各自的 `run_*.py` 中定義；若需要調整比對規則，在對應子模組中修改。
