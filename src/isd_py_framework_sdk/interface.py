"""
isd_py_framework_sdk.interface — 介面與核心設計模式的短路徑別名。

提供：
  - SingletonMetaclass          (from isd_py_framework_sdk.base.Singleton)
  - IScalableWindowTester       (from isd_py_framework_sdk.window_design_helper.IScalableWindowTester)

用法：
    from isd_py_framework_sdk.interface import SingletonMetaclass, IScalableWindowTester
"""

from .base.Singleton import SingletonMetaclass
from .window_design_helper.IScalableWindowTester import IScalableWindowTester

__all__ = [
    "SingletonMetaclass",
    "IScalableWindowTester",
]
