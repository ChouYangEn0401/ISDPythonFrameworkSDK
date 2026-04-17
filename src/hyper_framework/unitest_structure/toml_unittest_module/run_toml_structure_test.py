"""
TOML 檔案比對工具
=================
使用 Python 3.11+ 內建的 ``tomllib``。

Config 範例::

    {
        "target_path": "output.toml",
        "bench_path":  "expected.toml",
        "mask": {                                               # 選填
            "include_paths": ["$.database"],                     # 只比對這些路徑
            "exclude_paths": ["$.metadata.generated_at"],        # 跳過這些路徑
        }
    }
"""
import tomllib
from typing import Any, Dict

from .._shared import (
    deep_compare,
    print_compare_header,
    print_test_result,
)


def compare_toml_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    mask        = config.get("mask")

    print_compare_header("TOML", target_path, bench_path)

    with open(target_path, "rb") as f:
        target = tomllib.load(f)
    with open(bench_path, "rb") as f:
        bench = tomllib.load(f)

    exclude_paths = set(mask.get("exclude_paths", [])) if mask else None
    include_paths = (
        set(mask["include_paths"]) if mask and "include_paths" in mask else None
    )

    errors = deep_compare(target, bench, "$", None, exclude_paths, include_paths)

    max_display = config.get("max_display_errors", 15)
    return print_test_result("TOML 比對", errors, max_display=max_display)
