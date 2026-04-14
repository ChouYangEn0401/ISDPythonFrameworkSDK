"""
TXT 純文字檔案比對工具
=====================
Config 範例::

    {
        "target_path": "output.txt",
        "bench_path":  "expected.txt",
        "encoding":    "utf-8",             # 選填
        "strip":       true,                # 選填，比對前是否去除首尾空白
        "checks":      ["content", "line_count"],
        "mask": {                            # 選填
            "include_rows": [1, 2, 3],       # 1-indexed
            "exclude_rows": [10],
        }
    }
"""
from typing import Any, Dict

from .._shared import (
    colorize_diff,
    resolve_row_mask,
    print_compare_header,
    print_test_result,
)


def compare_txt_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    encoding    = config.get("encoding", "utf-8")
    strip       = config.get("strip", False)
    checks      = config.get("checks", ["content"])
    mask        = config.get("mask")

    print_compare_header("TXT", target_path, bench_path)

    with open(target_path, "r", encoding=encoding) as f:
        target_lines = [ln.rstrip("\n\r") for ln in f.readlines()]
    with open(bench_path, "r", encoding=encoding) as f:
        bench_lines = [ln.rstrip("\n\r") for ln in f.readlines()]

    errors: list = []

    # ── line_count ──
    if "line_count" in checks and len(target_lines) != len(bench_lines):
        errors.append(f"行數不同: {colorize_diff(len(target_lines), len(bench_lines))}")

    # ── content ──
    if "content" in checks:
        max_rows = max(len(target_lines), len(bench_lines))
        rows_to_check = resolve_row_mask(max_rows, mask)

        for r in sorted(rows_to_check):
            if r > len(target_lines):
                errors.append(f"第 {r} 行: 待測檔缺少此行")
                continue
            if r > len(bench_lines):
                errors.append(f"第 {r} 行: 標準檔無此行（多出）")
                continue

            tl = target_lines[r - 1]
            bl = bench_lines[r - 1]
            if strip:
                tl = tl.strip()
                bl = bl.strip()
            if tl != bl:
                errors.append(f"第 {r} 行: {colorize_diff(repr(tl), repr(bl))}")

    print_test_result("TXT 比對", errors)
    return not errors
