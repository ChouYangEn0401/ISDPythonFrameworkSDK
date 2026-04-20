#!/usr/bin/env python
"""
tools/run_file_tests.py
========================
批次執行所有檔案比對測試，並可輸出 HTML 差異報告。

Usage
-----
  python tools/run_file_tests.py suite.yaml
  python tools/run_file_tests.py suite.yaml --html report.html
  python tools/run_file_tests.py suite.json --html report.html --title "Sprint 42 回歸測試"

Exit codes
----------
  0  全部通過
  1  任一測試失敗
  2  config 檔案不存在或格式錯誤

Config 格式（YAML 或 JSON）
--------------------------
tests:
  # ── CSV ──
  - format: csv
    label: "月報 A"
    target_path: output/report_a.csv
    bench_path:  expected/report_a.csv
    checks: [content, row_count, column_count, header]
    mask:
      exclude_rows: [1]          # 跳過標題行（不比對）

  # ── JSON ──
  - format: json
    label: "API Response"
    target_path: output/response.json
    bench_path:  expected/response.json
    mask:
      exclude_paths: ["$.timestamp", "$.request_id"]

  # ── TXT ──
  - format: txt
    label: "Log Output"
    target_path: output/run.log
    bench_path:  expected/run.log
    strip: true
    checks: [content, line_count]
    mask:
      exclude_rows: [1]

  # ── Excel ──
  - format: excel
    label: "月報 Excel"
    target_path: output/monthly.xlsx
    bench_path:  expected/monthly.xlsx
    sheets:
      - target_sheet: Summary
        bench_sheet:  Summary
        checks: [content, color, freeze]
        mask:
          exclude_rows: [1]

支援格式: csv, json, jsonl, txt, yaml, xml, ini, toml, excel (xlsx)
"""

import sys
import argparse
import importlib
from pathlib import Path
from typing import Any, Dict, List

# ── allow running from the repo root without installing the package ───────
_here = Path(__file__).resolve().parent
_src = _here.parent / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

# ── format → (module, function) ──────────────────────────────────────────
_DISPATCH: Dict[str, tuple] = {
    "csv":   ("hyper_framework.file_compare.csv_unittest_module",   "compare_csv_files"),
    "json":  ("hyper_framework.file_compare.json_unittest_module",  "compare_json_files"),
    "jsonl": ("hyper_framework.file_compare.jsonl_unittest_module", "compare_jsonl_files"),
    "txt":   ("hyper_framework.file_compare.txt_unittest_module",   "compare_txt_files"),
    "yaml":  ("hyper_framework.file_compare.yaml_unittest_module",  "compare_yaml_files"),
    "yml":   ("hyper_framework.file_compare.yaml_unittest_module",  "compare_yaml_files"),
    "xml":   ("hyper_framework.file_compare.xml_unittest_module",   "compare_xml_files"),
    "ini":   ("hyper_framework.file_compare.ini_unittest_module",   "compare_ini_files"),
    "toml":  ("hyper_framework.file_compare.toml_unittest_module",  "compare_toml_files"),
    "excel": ("hyper_framework.file_compare.excel_unittest_module", "compare_excel_sheets"),
    "xlsx":  ("hyper_framework.file_compare.excel_unittest_module", "compare_excel_sheets"),
}


def _load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"ERROR: config file not found: {path}", file=sys.stderr)
        sys.exit(2)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            print("ERROR: pyyaml is required to load .yaml configs. "
                  "Run: pip install pyyaml", file=sys.stderr)
            sys.exit(2)
        return yaml.safe_load(text)
    import json
    return json.loads(text)


def _run_single(test: dict):
    from hyper_framework.file_compare._shared import CompareResult

    fmt = test.get("format", "").lower().lstrip(".")
    label = test.get("label", fmt)

    if fmt not in _DISPATCH:
        print(f"\n  ERROR: unknown format '{fmt}'", file=sys.stderr)
        return CompareResult(label=label, passed=False, errors=[f"Unknown format: {fmt}"])

    mod_name, fn_name = _DISPATCH[fmt]
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, fn_name)

    # Pass everything except the runner-specific keys to the comparison function
    cfg = {k: v for k, v in test.items() if k not in ("format", "label")}

    raw = fn(cfg)

    # Normalise to CompareResult (backward compat for any non-updated callers)
    if isinstance(raw, CompareResult):
        raw.label = label
        return raw
    return CompareResult(label=label, passed=bool(raw), errors=[])


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="批次執行檔案比對測試，可選輸出 HTML 差異報告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("config", help="測試 config 檔案路徑 (.yaml / .json)")
    parser.add_argument("--html", metavar="PATH", help="輸出 HTML 報告至此路徑")
    parser.add_argument(
        "--title", default="File Comparison Report", help="HTML 報告標題（預設: 'File Comparison Report'）"
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="遇到第一個失敗即停止"
    )
    args = parser.parse_args(argv)

    cfg = _load_config(args.config)
    tests = cfg.get("tests", [])

    if not tests:
        print("WARNING: config 中沒有任何 test 項目。", file=sys.stderr)
        return 0

    GREEN = "\033[92m"
    RED   = "\033[91m"
    BOLD  = "\033[1m"
    RESET = "\033[0m"

    results = []
    for test in tests:
        result = _run_single(test)
        results.append(result)
        if args.fail_fast and not result.passed:
            print(f"\n{RED}--fail-fast: 停止執行。{RESET}")
            break

    # ── terminal summary ──────────────────────────────────────────────────
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"\n{'─' * 50}")
    print(
        f"{BOLD}結果: "
        f"{GREEN}{passed} PASS{RESET}  "
        f"{RED}{failed} FAIL{RESET}"
        f"{BOLD}  （共 {len(results)} 項）{RESET}"
    )
    if failed:
        for r in results:
            if not r.passed:
                print(f"  {RED}✗{RESET} {r.label}")
    print(f"{'─' * 50}\n")

    # ── HTML report ───────────────────────────────────────────────────────
    if args.html:
        from hyper_framework.file_compare.html_report import generate_html_report
        generate_html_report(results, args.html, title=args.title)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
