"""file_compare — 多格式檔案比對工具，快速驗證輸出是否與預期一致.

This module provides lazy wrappers so optional backends such as YAML or
Excel (openpyxl) are only imported when the corresponding function is
actually called. This avoids raising ModuleNotFoundError at package
import time.

Usage (examples):
  from hyper_framework.file_compare import compare_toml_files
  import hyper_framework.file_compare.toml_unittest_module as t; t.compare_toml_files(...)
  from hyper_framework.file_compare.toml_unittest_module import compare_toml_files
"""

from importlib import import_module
from typing import Any


def _lazy_attr(module_name: str, attr: str) -> Any:
    mod = import_module(f".{module_name}", __package__)
    return getattr(mod, attr)


def compare_csv_files(*args, **kwargs):
    return _lazy_attr("csv_unittest_module", "compare_csv_files")(*args, **kwargs)


def compare_excel_sheets(*args, **kwargs):
    return _lazy_attr("excel_unittest_module", "compare_excel_sheets")(*args, **kwargs)


def compare_ini_files(*args, **kwargs):
    return _lazy_attr("ini_unittest_module", "compare_ini_files")(*args, **kwargs)


def compare_json_files(*args, **kwargs):
    return _lazy_attr("json_unittest_module", "compare_json_files")(*args, **kwargs)


def compare_jsonl_files(*args, **kwargs):
    return _lazy_attr("jsonl_unittest_module", "compare_jsonl_files")(*args, **kwargs)


def compare_toml_files(*args, **kwargs):
    return _lazy_attr("toml_unittest_module", "compare_toml_files")(*args, **kwargs)


def compare_txt_files(*args, **kwargs):
    return _lazy_attr("txt_unittest_module", "compare_txt_files")(*args, **kwargs)


def compare_xml_files(*args, **kwargs):
    return _lazy_attr("xml_unittest_module", "compare_xml_files")(*args, **kwargs)


def compare_yaml_files(*args, **kwargs):
    return _lazy_attr("yaml_unittest_module", "compare_yaml_files")(*args, **kwargs)


__all__ = [
    "compare_csv_files",
    "compare_excel_sheets",
    "compare_ini_files",
    "compare_json_files",
    "compare_jsonl_files",
    "compare_toml_files",
    "compare_txt_files",
    "compare_xml_files",
    "compare_yaml_files",
]
