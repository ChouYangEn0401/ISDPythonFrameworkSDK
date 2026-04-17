"""
JSONL 結構比對測試 — sample demo
==================================
使用 hyper_framework 的 compare_jsonl_files，
以 tests/test_file/base/sample.jsonl 作為待測檔，
    tests/test_file/base/[BU] sample.jsonl 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_jsonl.py
"""
from pathlib import Path
from hyper_framework.unitest_structure.jsonl_unittest_module import compare_jsonl_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.jsonl"),
    "bench_path":  str(BASE / "[BU] sample.jsonl"),
    "encoding":    "utf-8",
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "include_rows": [1, 2],  # 1-indexed，只比對這些 JSONL 行
    #     "exclude_rows": [],
    # },
}

if __name__ == "__main__":
    compare_jsonl_files(TEST_CONFIG)
