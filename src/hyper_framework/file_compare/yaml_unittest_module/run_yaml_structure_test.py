"""
YAML 檔案比對工具
=================
需安裝 ``pyyaml`` (``pip install pyyaml``)。

Config 範例::

    {
        "target_path": "output.yaml",
        "bench_path":  "expected.yaml",
        "encoding":    "utf-8",                        # 選填
        "mask": {                                       # 選填
            "include_paths": ["$.settings"],             # 只比對這些路徑
            "exclude_paths": ["$.generated_at"],         # 跳過這些路徑
        }
    }
"""
import yaml  # type: ignore[import-untyped]
from typing import Any, Dict

from .._shared import (
    deep_compare,
    print_compare_header,
    print_test_result,
)


def compare_yaml_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    encoding    = config.get("encoding", "utf-8")
    mask        = config.get("mask")

    print_compare_header("YAML", target_path, bench_path)

    with open(target_path, "r", encoding=encoding) as f:
        target = yaml.safe_load(f)
    with open(bench_path, "r", encoding=encoding) as f:
        bench = yaml.safe_load(f)

    exclude_paths = set(mask.get("exclude_paths", [])) if mask else None
    include_paths = (
        set(mask["include_paths"]) if mask and "include_paths" in mask else None
    )

    errors = deep_compare(target, bench, "$", None, exclude_paths, include_paths)

    max_display = config.get("max_display_errors", 15)
    return print_test_result("YAML 比對", errors, max_display=max_display)
