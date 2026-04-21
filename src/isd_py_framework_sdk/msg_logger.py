"""
isd_py_framework_sdk.msg_logger — 日誌系統的短路徑別名。

等同於從 isd_py_framework_sdk.message_logger 匯入，提供更簡潔的 namespace：
    from isd_py_framework_sdk.msg_logger import SingletonSystemLogger, DarkThemeTerminalAdapter, ...
"""

from .message_logger import (
    LogLevelLiteral,
    LevelOrder,
    LoggerAdapterBase,
    TerminalAdapter,
    DarkThemeTerminalAdapter,
    LightThemeTerminalAdapter,
    FileAdapter,
    TkinterAdapter,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
    LoggerBase,
    SingletonSystemLogger,
)

__all__ = [
    "LogLevelLiteral",
    "LevelOrder",
    "LoggerAdapterBase",
    "TerminalAdapter",
    "DarkThemeTerminalAdapter",
    "LightThemeTerminalAdapter",
    "FileAdapter",
    "TkinterAdapter",
    "DarkThemeTkinterAdapter",
    "LightThemeTkinterAdapter",
    "LoggerBase",
    "SingletonSystemLogger",
]
