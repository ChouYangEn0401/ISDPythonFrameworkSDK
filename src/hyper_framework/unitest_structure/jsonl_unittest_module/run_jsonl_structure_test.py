"""
JSONL (JSON Lines) 檔案比對工具
===============================
Config 範例::

    {
        "target_path": "output.jsonl",
        "bench_path":  "expected.jsonl",
        "encoding":    "utf-8",             # 選填
        "mask": {                            # 選填
            "include_rows": [1, 3, 5],       # 1-indexed
            "exclude_rows": [2],
        }
    }
"""
import json
from typing import Any, Dict

from .._shared import (
    colorize_diff,
    resolve_row_mask,
    deep_compare,
    print_compare_header,
    print_test_result,
)


def compare_jsonl_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    encoding    = config.get("encoding", "utf-8")
    mask        = config.get("mask")

    print_compare_header("JSONL", target_path, bench_path)

    with open(target_path, "r", encoding=encoding) as f:
        target_lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    with open(bench_path, "r", encoding=encoding) as f:
        bench_lines = [ln.rstrip("\n") for ln in f if ln.strip()]

    errors: list = []

    max_rows = max(len(target_lines), len(bench_lines))
    if len(target_lines) != len(bench_lines):
        errors.append(f"行數不同: {colorize_diff(len(target_lines), len(bench_lines))}")

    rows_to_check = resolve_row_mask(max_rows, mask)

    for r in sorted(rows_to_check):
        if r > len(target_lines):
            errors.append(f"第 {r} 行: 待測檔缺少此行")
            continue
        if r > len(bench_lines):
            errors.append(f"第 {r} 行: 標準檔無此行（多出）")
            continue

        try:
            t_obj = json.loads(target_lines[r - 1])
        except json.JSONDecodeError as exc:
            errors.append(f"第 {r} 行: 待測檔 JSON 解析錯誤 — {exc}")
            continue
        try:
            b_obj = json.loads(bench_lines[r - 1])
        except json.JSONDecodeError as exc:
            errors.append(f"第 {r} 行: 標準檔 JSON 解析錯誤 — {exc}")
            continue

        line_errors = deep_compare(t_obj, b_obj, f"L{r}")
        errors.extend(line_errors)

    print_test_result("JSONL 比對", errors)
    return not errors
