"""
TOML 結構比對測試 — sample demo
==================================
使用 hyper_framework 的 compare_toml_files（需 Python 3.11+）。
以 tests/test_file/base/sample.toml 作為待測檔，
    tests/test_file/base/[BU] sample.toml 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_toml.py
"""
from pathlib import Path
from hyper_framework.file_compare.toml_unittest_module import compare_toml_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.toml"),
    "bench_path":  str(BASE / "[BU] sample.toml"),
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "include_paths": ["$.meta"],
    #     "exclude_paths": ["$.meta.generated_at"],
    # },
}

if __name__ == "__main__":
    compare_toml_files(TEST_CONFIG)
