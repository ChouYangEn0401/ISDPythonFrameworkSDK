"""
CSV 結構比對測試 — sample demo
================================
使用 hyper_framework 的 compare_csv_files，
以 tests/test_file/base/sample.csv 作為待測檔，
    tests/test_file/base/[BU] sample.csv 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_csv.py
"""
from pathlib import Path
from hyper_framework.unitest_structure.csv_unittest_module import compare_csv_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.csv"),
    "bench_path":  str(BASE / "[BU] sample.csv"),
    "encoding":    "utf-8",
    "delimiter":   ",",
    "checks":      ["content", "row_count", "column_count", "header"],
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "include_rows": [1, 2, 3],   # 1-indexed，只比對這些行
    #     "exclude_rows": [],
    #     "include_cols": [0, 1, 2],   # 0-indexed，只比對這些欄
    #     "exclude_cols": [],
    # },
}

if __name__ == "__main__":
    compare_csv_files(TEST_CONFIG)
