"""
XML 結構比對測試 — sample demo
================================
使用 hyper_framework 的 compare_xml_files，
以 tests/test_file/base/sample.xml 作為待測檔，
    tests/test_file/base/[BU] sample.xml 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_xml.py
"""
from pathlib import Path
from hyper_framework.file_compare.xml_unittest_module import compare_xml_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.xml"),
    "bench_path":  str(BASE / "[BU] sample.xml"),
    "encoding":    "utf-8",
    "checks":      ["tag", "text", "attrib", "children_count"],
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "exclude_tags": ["timestamp", "generated"],
    # },
}

if __name__ == "__main__":
    compare_xml_files(TEST_CONFIG)
