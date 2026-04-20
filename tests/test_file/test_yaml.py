"""
YAML 結構比對測試 — sample demo
==================================
使用 hyper_framework 的 compare_yaml_files（需安裝 pyyaml）。
以 tests/test_file/base/sample.yaml 作為待測檔，
    tests/test_file/base/[BU] sample.yaml 作為標準備份。

執行方式（安裝 wheel 之後）：
    python tests/test_file/test_yaml.py
"""
from pathlib import Path
import pytest

# Skip if YAML backend is not installed
pytest.importorskip("yaml")

from hyper_framework.file_compare import compare_yaml_files

BASE = Path(__file__).parent / "base"

TEST_CONFIG = {
    "target_path": str(BASE / "sample.yaml"),
    "bench_path":  str(BASE / "[BU] sample.yaml"),
    "encoding":    "utf-8",
    # 以下為 mask 範例，可視需要取消註解：
    # "mask": {
    #     "include_paths": ["$.items"],
    #     "exclude_paths": ["$.meta.generated_by"],
    # },
}

if __name__ == "__main__":
    compare_yaml_files(TEST_CONFIG)
