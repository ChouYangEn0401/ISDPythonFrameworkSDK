"""
CSV 檔案比對工具
================
Config 範例::

    {
        "target_path": "output.csv",
        "bench_path":  "expected.csv",
        "encoding":    "utf-8",          # 選填，預設 utf-8
        "delimiter":   ",",              # 選填，預設 ","
        "checks":      ["content", "row_count", "column_count", "header"],
        "mask": {                        # 選填
            "include_rows": [1, 2, 3],   # 1-indexed，只比對這些行
            "exclude_rows": [5],         # 跳過這些行
            "include_cols": [0, 2],      # 0-indexed，只比對這些欄
            "exclude_cols": [1],         # 跳過這些欄
        }
    }
"""
import csv
from typing import Any, Dict

from .._shared import (
    colorize_diff,
    resolve_row_mask,
    print_compare_header,
    print_test_result,
)


def compare_csv_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    encoding    = config.get("encoding", "utf-8")
    delimiter   = config.get("delimiter", ",")
    checks      = config.get("checks", ["content"])
    mask        = config.get("mask")

    print_compare_header("CSV", target_path, bench_path)

    with open(target_path, "r", encoding=encoding, newline="") as f:
        target_rows = list(csv.reader(f, delimiter=delimiter))
    with open(bench_path, "r", encoding=encoding, newline="") as f:
        bench_rows = list(csv.reader(f, delimiter=delimiter))

    errors: list = []

    # ── row_count ──
    if "row_count" in checks and len(target_rows) != len(bench_rows):
        errors.append(f"行數不同: {colorize_diff(len(target_rows), len(bench_rows))}")

    # ── column_count（以第一行為準） ──
    if "column_count" in checks and target_rows and bench_rows:
        tc, bc = len(target_rows[0]), len(bench_rows[0])
        if tc != bc:
            errors.append(f"欄數不同: {colorize_diff(tc, bc)}")

    # ── header ──
    if "header" in checks and target_rows and bench_rows:
        if target_rows[0] != bench_rows[0]:
            errors.append(f"標題行不同: {colorize_diff(target_rows[0], bench_rows[0])}")

    # ── content ──
    if "content" in checks:
        max_rows = max(len(target_rows), len(bench_rows))
        rows_to_check = resolve_row_mask(max_rows, mask)

        # column mask
        include_cols = set(mask["include_cols"]) if mask and "include_cols" in mask else None
        exclude_cols = set(mask.get("exclude_cols", [])) if mask else set()

        for r in sorted(rows_to_check):
            if r > len(target_rows):
                errors.append(f"第 {r} 行: 待測檔缺少此行")
                continue
            if r > len(bench_rows):
                errors.append(f"第 {r} 行: 標準檔無此行（多出）")
                continue

            t_row = target_rows[r - 1]
            b_row = bench_rows[r - 1]
            max_c = max(len(t_row), len(b_row))

            for ci in range(max_c):
                if include_cols is not None and ci not in include_cols:
                    continue
                if ci in exclude_cols:
                    continue

                tv = t_row[ci] if ci < len(t_row) else ""
                bv = b_row[ci] if ci < len(b_row) else ""
                if tv != bv:
                    errors.append(
                        f"第 {r} 行, 第 {ci + 1} 欄: "
                        + colorize_diff(repr(tv), repr(bv))
                    )

    print_test_result("CSV 比對", errors)
    return not errors
