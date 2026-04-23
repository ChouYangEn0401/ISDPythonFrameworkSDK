"""
isd_py_framework_sdk.path_manager
==================================

Central, environment-aware path management for ISD projects.
針對 ISD 專案的集中式、環境感知路徑管理。

Public API
----------
``SingletonPathManager``
    The main singleton you interact with.  Configure once at startup;
    query from anywhere.
    你主要互動的單例。啟動時設定一次；在任何地方查詢。

``IPathManager``
    Abstract interface.  Subclass to build project-specific managers
    that plug into the same ecosystem.
    抽象介面。子類化以建立專案專用的管理器並整合進同一生態系。

``PathMode``
    Enum controlling how a path is anchored / expressed
    (``ABSOLUTE``, ``PROJ_RELATIVE``, ``EXE_INNER``, …).
    列舉，控制路徑如何定位/表達（`ABSOLUTE`、`PROJ_RELATIVE`、`EXE_INNER` 等）。

``Waterfall``
    Ordered fallback chain: ``get(tag, Waterfall.UNIVERSAL)`` tries
    each anchor in sequence and returns the first existing path.
    有序回退鏈：``get(tag, Waterfall.UNIVERSAL)`` 會依序嘗試每個定位點，並回傳第一個存在的路徑。

衝突處理策略
Conflict strategies
-------------------
``ConflictStrategy``           — abstract base  ;;  抽象基底
``OverwriteStrategy``          — silently overwrite  ;;  直接覆寫
``SkipIfExistsStrategy``       — skip if already there  ;;  若已存在則跳過
``TimestampSuffixStrategy``    — append ``_YYYYMMDD_HHMMSS``  ;;  附加時間戳後綴 `_YYYYMMDD_HHMMSS`
``IncrementSuffixStrategy``    — append ``_001``, ``_002``, …  ;;  附加遞增後綴 `_001`、`_002`、…

Internal
--------
``PathEntry``  — single registry record (tag + stored_path + anchor)  ;;  單一註冊記錄（tag + stored_path + anchor）
``EnvironmentResolver`` — static helpers for anchor directories  ;;  提供定位目錄的靜態輔助函式
"""

from ._enums import PathMode
from ._waterfall import Waterfall, ResolveIntent, WaterfallTrace, Attempt, PRESETS
from ._resolver import EnvironmentResolver
from ._conflict import (
    ConflictStrategy,
    OverwriteStrategy,
    SkipIfExistsStrategy,
    TimestampSuffixStrategy,
    IncrementSuffixStrategy,
)
from ._registry import PathEntry
from .interface import IPathManager
from .singleton_path_manager import SingletonPathManager

__all__ = [
    # Core
    "SingletonPathManager",
    "IPathManager",
    "PathMode",
    "Waterfall",
    "PRESETS",
    "ResolveIntent",
    "WaterfallTrace",
    "Attempt",
    # Conflict strategies
    "ConflictStrategy",
    "OverwriteStrategy",
    "SkipIfExistsStrategy",
    "TimestampSuffixStrategy",
    "IncrementSuffixStrategy",
    # Helpers (exposed for subclassing / advanced use)
    "PathEntry",
    "EnvironmentResolver",
]
