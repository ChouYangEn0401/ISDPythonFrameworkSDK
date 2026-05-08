"""
isd_py_framework_sdk.msg_logger - short alias for message_logger.

This module mirrors the stable public API from
``isd_py_framework_sdk.message_logger``.
"""

from .message_logger import (
    LogLevelLiteral,
    LevelOrder,
    SingletonSystemLogger,
    get_logger,
    configure_logger,
    LoggerAdapterBase,
    DarkThemeTerminalAdapter,
    LightThemeTerminalAdapter,
    FileAdapter,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
    DarkThemeTkLabelAdapter,
    LightThemeTkLabelAdapter,
    DarkThemeTtkLabelAdapter,
    LightThemeTtkLabelAdapter,
    LocalHTTPAdapter,
    QueuedSocketAdapter,
    # Compatibility names; intentionally omitted from __all__.
    LoggerBase,
    AbstractTerminalAdapterBase,
    AbstractTkinterAdapterBase,
    TkLabelAdapter,
    TtkLabelAdapter,
    HTMLAdapter,
    HTTPAdapter,
    DBAdapter,
    WebsocketAdapter,
)

__all__ = [
    "LogLevelLiteral",
    "LevelOrder",
    "SingletonSystemLogger",
    "get_logger",
    "configure_logger",
    "LoggerAdapterBase",
    "DarkThemeTerminalAdapter",
    "LightThemeTerminalAdapter",
    "FileAdapter",
    "DarkThemeTkinterAdapter",
    "LightThemeTkinterAdapter",
    "DarkThemeTkLabelAdapter",
    "LightThemeTkLabelAdapter",
    "DarkThemeTtkLabelAdapter",
    "LightThemeTtkLabelAdapter",
    "LocalHTTPAdapter",
    "QueuedSocketAdapter",
]
