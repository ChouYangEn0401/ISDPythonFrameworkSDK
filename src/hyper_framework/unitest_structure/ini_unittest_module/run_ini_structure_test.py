"""
INI 檔案比對工具
================
Config 範例::

    {
        "target_path": "output.ini",
        "bench_path":  "expected.ini",
        "encoding":    "utf-8",                                # 選填
        "mask": {                                               # 選填
            "include_sections": ["database", "server"],         # 只比對這些區段
            "exclude_sections": ["debug"],                      # 跳過這些區段
            "exclude_keys":    {"server": ["timestamp"]},       # 跳過特定 key
        }
    }
"""
import configparser
from typing import Any, Dict

from .._shared import (
    colorize_diff,
    print_compare_header,
    print_test_result,
)


def compare_ini_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    encoding    = config.get("encoding", "utf-8")
    mask        = config.get("mask")

    print_compare_header("INI", target_path, bench_path)

    t_cfg = configparser.ConfigParser()
    t_cfg.read(target_path, encoding=encoding)
    b_cfg = configparser.ConfigParser()
    b_cfg.read(bench_path, encoding=encoding)

    include_sections = (
        set(mask["include_sections"]) if mask and "include_sections" in mask else None
    )
    exclude_sections = set(mask.get("exclude_sections", [])) if mask else set()
    exclude_keys = mask.get("exclude_keys", {}) if mask else {}

    errors: list = []
    all_sections = sorted(set(t_cfg.sections()) | set(b_cfg.sections()))

    for sec in all_sections:
        if include_sections is not None and sec not in include_sections:
            continue
        if sec in exclude_sections:
            continue

        if sec not in t_cfg:
            errors.append(f"[{sec}] 區段: 待測檔缺少此區段")
            continue
        if sec not in b_cfg:
            errors.append(f"[{sec}] 區段: 標準檔無此區段（多出）")
            continue

        sec_exclude = set(exclude_keys.get(sec, []))
        all_keys = sorted(set(t_cfg[sec].keys()) | set(b_cfg[sec].keys()))

        for key in all_keys:
            if key in sec_exclude:
                continue
            tv = t_cfg[sec].get(key)
            bv = b_cfg[sec].get(key)
            if tv is None:
                errors.append(f"[{sec}].{key}: 待測檔缺少此 key")
            elif bv is None:
                errors.append(f"[{sec}].{key}: 標準檔無此 key（多出）")
            elif tv != bv:
                errors.append(f"[{sec}].{key}: {colorize_diff(repr(tv), repr(bv))}")

    return print_test_result("INI 比對", errors)
