"""
XML 檔案比對工具
================
Config 範例::

    {
        "target_path": "output.xml",
        "bench_path":  "expected.xml",
        "encoding":    "utf-8",                                  # 選填
        "checks":      ["tag", "text", "attrib", "children_count"],
        "mask": {                                                 # 選填
            "exclude_tags": ["timestamp", "generated"],           # 跳過這些 tag
        }
    }
"""
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set

from .._shared import (
    colorize_diff,
    print_compare_header,
    print_test_result,
)


def _compare_elements(
    t_elem: ET.Element,
    b_elem: ET.Element,
    path: str,
    checks: List[str],
    errors: list,
    exclude_tags: Optional[Set[str]] = None,
):
    """Recursively compare two XML elements."""
    if exclude_tags and t_elem.tag in exclude_tags:
        return

    # tag
    if "tag" in checks and t_elem.tag != b_elem.tag:
        errors.append((path, "標籤不同", t_elem.tag, b_elem.tag))
        return  # subtree comparison meaningless

    # attrib
    if "attrib" in checks and t_elem.attrib != b_elem.attrib:
        errors.append((path, "屬性不同", str(t_elem.attrib), str(b_elem.attrib)))

    # text
    if "text" in checks:
        tt = (t_elem.text or "").strip()
        bt = (b_elem.text or "").strip()
        if tt != bt:
            errors.append((path, "文字內容不同", repr(tt), repr(bt)))

        t_tail = (t_elem.tail or "").strip()
        b_tail = (b_elem.tail or "").strip()
        if t_tail != b_tail:
            errors.append((path + "/@tail", "尾部文字不同", repr(t_tail), repr(b_tail)))

    # children
    t_children = list(t_elem)
    b_children = list(b_elem)
    if "children_count" in checks and len(t_children) != len(b_children):
        errors.append((path, "子元素數量不同", len(t_children), len(b_children)))

    for i in range(min(len(t_children), len(b_children))):
        child_path = f"{path}/{b_children[i].tag}[{i}]"
        _compare_elements(
            t_children[i], b_children[i], child_path, checks, errors, exclude_tags
        )


def compare_xml_files(config: Dict[str, Any]) -> bool:
    target_path = config["target_path"]
    bench_path  = config["bench_path"]
    checks      = config.get("checks", ["tag", "text", "attrib", "children_count"])
    mask        = config.get("mask")

    print_compare_header("XML", target_path, bench_path)

    t_tree = ET.parse(target_path)
    b_tree = ET.parse(bench_path)

    exclude_tags = set(mask.get("exclude_tags", [])) if mask else None

    errors: list = []
    _compare_elements(t_tree.getroot(), b_tree.getroot(), "/", checks, errors, exclude_tags)

    max_display = config.get("max_display_errors", 15)
    return print_test_result("XML 比對", errors, max_display=max_display)
