"""
INI 結構比對測試 — sample demo
================================
使用 isd_py_framework_sdk 的 compare_ini_files，
以 tests/test_file/base/sample.ini 作為待測檔，
    tests/test_file/base/[BU] sample.ini 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_ini.py
"""
from pathlib import Path
from isd_py_framework_sdk.file_compare import compare_ini_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.ini"),
    "bench_path":  str(BASE / "[BU] sample.ini"),
    "encoding":    "utf-8",
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "include_sections": ["server"],
    #     "exclude_sections": ["meta"],
    #     "exclude_keys":     {"server": ["timestamp"]},
    # },
}

if __name__ == "__main__":
    compare_ini_files(TEST_CONFIG)
