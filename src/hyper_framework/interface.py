"""
hyper_framework.interface — 介面與核心設計模式的短路徑別名。

提供：
  - SingletonMetaclass          (from hyper_framework.base.Singleton)
  - IScalableWindowTester       (from hyper_framework.window_design_helper.IScalableWindowTester)

用法：
    from hyper_framework.interface import SingletonMetaclass, IScalableWindowTester
"""

from .base.Singleton import SingletonMetaclass
from .window_design_helper.IScalableWindowTester import IScalableWindowTester

__all__ = [
    "SingletonMetaclass",
    "IScalableWindowTester",
]
