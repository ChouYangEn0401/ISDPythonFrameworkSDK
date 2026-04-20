"""
全格式一鍵測試 — run all sample demos
=======================================
一次執行所有支援格式的比對測試，最後彙整顯示通過 / 失敗。

執行方式（安裝 wheel 之後）：
    python tests/test_file/run_all.py
"""
from pathlib import Path

from hyper_framework.file_compare.csv_unittest_module   import compare_csv_files
from hyper_framework.file_compare.excel_unittest_module import compare_excel_sheets
from hyper_framework.file_compare.json_unittest_module  import compare_json_files
from hyper_framework.file_compare.jsonl_unittest_module import compare_jsonl_files
from hyper_framework.file_compare.txt_unittest_module   import compare_txt_files
from hyper_framework.file_compare.xml_unittest_module   import compare_xml_files
from hyper_framework.file_compare.ini_unittest_module   import compare_ini_files
from hyper_framework.file_compare.toml_unittest_module  import compare_toml_files
from hyper_framework.file_compare.yaml_unittest_module  import compare_yaml_files

BASE = Path(__file__).parent / "base"

# ── 各格式 config ─────────────────────────────────────────────────────────

CSV_CONFIG = {
    "target_path": str(BASE / "sample.csv"),
    "bench_path":  str(BASE / "[BU] sample.csv"),
    "encoding":    "utf-8",
    "delimiter":   ",",
    "checks":      ["content", "row_count", "column_count", "header"],
}

EXCEL_CONFIG = {
    "target_path": str(BASE / "sample.xlsx"),
    "bench_path":  str(BASE / "[BU] sample.xlsx"),
    "sheets": [
        {
            "target_sheet": "Sheet",
            "bench_sheet":  "Sheet",
            "checks": ["content", "freeze", "hidden", "color"],
        },
    ],
}

JSON_CONFIG = {
    "target_path": str(BASE / "sample.json"),
    "bench_path":  str(BASE / "[BU] sample.json"),
    "encoding":    "utf-8",
}

JSONL_CONFIG = {
    "target_path": str(BASE / "sample.jsonl"),
    "bench_path":  str(BASE / "[BU] sample.jsonl"),
    "encoding":    "utf-8",
}

TXT_CONFIG = {
    "target_path": str(BASE / "sample.txt"),
    "bench_path":  str(BASE / "[BU] sample.txt"),
    "encoding":    "utf-8",
    "strip":       False,
    "checks":      ["content", "line_count"],
}

XML_CONFIG = {
    "target_path": str(BASE / "sample.xml"),
    "bench_path":  str(BASE / "[BU] sample.xml"),
    "encoding":    "utf-8",
    "checks":      ["tag", "text", "attrib", "children_count"],
}

INI_CONFIG = {
    "target_path": str(BASE / "sample.ini"),
    "bench_path":  str(BASE / "[BU] sample.ini"),
    "encoding":    "utf-8",
}

TOML_CONFIG = {
    "target_path": str(BASE / "sample.toml"),
    "bench_path":  str(BASE / "[BU] sample.toml"),
}

YAML_CONFIG = {
    "target_path": str(BASE / "sample.yaml"),
    "bench_path":  str(BASE / "[BU] sample.yaml"),
    "encoding":    "utf-8",
}

# ── 執行 ──────────────────────────────────────────────────────────────────

RESET = "\033[0m"
GREEN = "\033[92m"
RED   = "\033[91m"
BOLD  = "\033[1m"


def _run(label: str, fn, cfg) -> bool:
    print(f"\n{'='*55}")
    print(f"  {BOLD}{label}{RESET}")
    print(f"{'='*55}")
    result = fn(cfg)
    # compare_excel_sheets returns None; treat as pass when no exception raised
    if result is None:
        return True
    return bool(result)


if __name__ == "__main__":
    suite = [
        ("CSV",   compare_csv_files,   CSV_CONFIG),
        ("Excel", compare_excel_sheets, EXCEL_CONFIG),
        ("JSON",  compare_json_files,   JSON_CONFIG),
        ("JSONL", compare_jsonl_files,  JSONL_CONFIG),
        ("TXT",   compare_txt_files,    TXT_CONFIG),
        ("XML",   compare_xml_files,    XML_CONFIG),
        ("INI",   compare_ini_files,    INI_CONFIG),
        ("TOML",  compare_toml_files,   TOML_CONFIG),
        ("YAML",  compare_yaml_files,   YAML_CONFIG),
    ]

    results = {}
    for label, fn, cfg in suite:
        try:
            results[label] = _run(label, fn, cfg)
        except Exception as exc:
            print(f"  {RED}ERROR: {exc}{RESET}")
            results[label] = False

    # ── 彙整 ──
    print(f"\n{'='*55}")
    print(f"  {BOLD}總結{RESET}")
    print(f"{'='*55}")
    all_pass = True
    for label, passed in results.items():
        mark = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {mark}  {label}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print(f"{GREEN}{BOLD}All tests PASSED.{RESET}")
    else:
        print(f"{RED}{BOLD}Some tests FAILED.{RESET}")
        raise SystemExit(1)
