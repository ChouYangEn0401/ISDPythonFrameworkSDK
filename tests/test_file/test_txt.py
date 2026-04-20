"""
TXT 純文字比對測試 — sample demo
===================================
使用 hyper_framework 的 compare_txt_files，
以 tests/test_file/base/sample.txt 作為待測檔，
    tests/test_file/base/[BU] sample.txt 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_txt.py
"""
from pathlib import Path
from hyper_framework.file_compare import compare_txt_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.txt"),
    "bench_path":  str(BASE / "[BU] sample.txt"),
    "encoding":    "utf-8",
    "strip":       False,
    "case":        "upper",
    "checks":      ["content", "line_count"],
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "include_rows": [1, 2, 3],  # 1-indexed，只比對這些行
    #     "exclude_rows": [],
    # },
}

if __name__ == "__main__":
    compare_txt_files(TEST_CONFIG)
