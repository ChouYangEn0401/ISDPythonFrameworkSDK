"""
hyper_framework.msg_logger — 日誌系統的短路徑別名。

等同於從 hyper_framework.message_logger 匯入，提供更簡潔的 namespace：
    from hyper_framework.msg_logger import SingletonSystemLogger, DarkThemeTerminalAdapter, ...
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
