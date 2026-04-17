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
from hyper_framework.unitest_structure.excel_unittest_module import compare_excel_sheets

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.xlsx"),
    "bench_path":  str(BASE / "[BU] sample.xlsx"),
    # 全域錯誤顯示數量（預設 15）。可在每個 sheet 中覆寫：sheet_conf['max_display']
    "max_display": 15,
    "sheets": [
        {
            "target_sheet": "Sheet",
            "bench_sheet":  "Sheet",
            "checks": ["content", "freeze", "hidden", "color"],
            # 以下為 mask 範例，可視需要取消註解：
            # "mask": {
            #     "include_rows": [1, 2, 3],            # 只比對這些行（1-indexed）
            #     "exclude_rows": [],
            #     "include_cols": ["A", "B", "C"],      # 只比對這些欄
            #     "exclude_cols": [],
            #     "exclude_cells": ["A1"],              # 跳過特定儲存格
            # },
            # "marker": {
            #     "known_correct":   ["A1", "B2"],     # 版本更新的正確改動 → 計入「已確認正確改動」
            #     "known_incorrect": ["C3"],           # 已確認問題               → 計入「已確認問題」
            # },
        },
    ],
}

if __name__ == "__main__":
    compare_excel_sheets(TEST_CONFIG)
