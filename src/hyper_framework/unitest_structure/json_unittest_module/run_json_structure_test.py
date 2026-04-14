"""
JSON 檔案比對工具
=================
Config 範例::

    {
        "target_path": "output.json",
        "bench_path":  "expected.json",
        "encoding":    "utf-8",                      # 選填
        "mask": {                                     # 選填
            "include_paths": ["$.data", "$.meta"],    # 只比對這些路徑
            "exclude_paths": ["$.timestamp"],          # 跳過這些路徑
        }
    }
"""
import json
from typing import Any, Dict

from .._shared import (
    deep_compare,
    print_compare_header,
    print_test_result,
)


def compare_json_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    encoding    = config.get("encoding", "utf-8")
    mask        = config.get("mask")

    print_compare_header("JSON", target_path, bench_path)

    with open(target_path, "r", encoding=encoding) as f:
        target = json.load(f)
    with open(bench_path, "r", encoding=encoding) as f:
        bench = json.load(f)

    exclude_paths = set(mask.get("exclude_paths", [])) if mask else None
    include_paths = (
        set(mask["include_paths"]) if mask and "include_paths" in mask else None
    )

    errors = deep_compare(target, bench, "$", None, exclude_paths, include_paths)

    return print_test_result("JSON 比對", errors)
