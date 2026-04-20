"""
hyper_framework.assertions — 斷言工具的短路徑別名。

等同於從 hyper_framework.helpers.assertions 匯入：
    from hyper_framework.assertions import assert__is_str, assert__is_int, ...
"""

from .helpers.assertions import *  # noqa: F401, F403
from .helpers.assertions import __all__
