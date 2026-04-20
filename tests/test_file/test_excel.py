"""
Excel 結構比對測試 — sample demo
=================================
使用 hyper_framework 的 compare_excel_sheets，
以 tests/test_file/base/sample.xlsx 作為待測檔，
    tests/test_file/base/[BU] sample.xlsx 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_excel.py
"""
from pathlib import Path
import pytest

# Skip if Excel backends are not installed
pytest.importorskip("openpyxl")
pytest.importorskip("pandas")

from hyper_framework.file_compare import compare_excel_sheets

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.xlsx"),
    "bench_path":  str(BASE / "[BU] sample.xlsx"),
    "sheets": [
        {
            "target_sheet": "Sheet",
            "bench_sheet":  "Sheet",
            "checks": ["content", "freeze", "hidden", "color"],
            # 以下為 mask 範例，可視需要取消註解：
            "mask": {
                # "include_rows": [1, 2, 3],      # 只比對這些行（1-indexed）
                "exclude_rows": [5, 6],
                "include_cols": ["A", "B", "D", "E", "F"], # 只比對這些欄
                # "exclude_cols": [],
                # "exclude_cells": ["A1"],          # 跳過特定儲存格
            },
            "skip": {
                "correct": ["E1"],   # 預期中的改動（不計入錯誤）
                "false":   [],   # 已知假錯誤（不計入錯誤）
            },
        },
    ],
}

if __name__ == "__main__":
    compare_excel_sheets(TEST_CONFIG)
