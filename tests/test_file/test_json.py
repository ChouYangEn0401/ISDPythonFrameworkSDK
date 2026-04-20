"""
JSON 結構比對測試 — sample demo
=================================
使用 hyper_framework 的 compare_json_files，
以 tests/test_file/base/sample.json 作為待測檔，
    tests/test_file/base/[BU] sample.json 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_json.py
"""
from pathlib import Path
from hyper_framework.file_compare.json_unittest_module import compare_json_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.json"),
    "bench_path":  str(BASE / "[BU] sample.json"),
    "encoding":    "utf-8",
    # 以下為 mask 範例，可視需要取消註解：
    "mask": {
        "include_paths": ["$.items"],  # 以 JSONPath-like 標記要比對的路徑
        "exclude_paths": [],
    },
    # 可用於控制錯誤顯示數量（預設 15）：
    # "max_display_errors": 20,
}

if __name__ == "__main__":
    compare_json_files(TEST_CONFIG)
