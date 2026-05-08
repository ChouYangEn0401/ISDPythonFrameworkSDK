"""
message_logger — 結構化多 adapter 日誌套件

公開 API（穩定）：
    SingletonSystemLogger   全域單例 logger
    LoggerBase              可繼承的 logger 基底
    LoggerAdapterBase       自訂 adapter 需繼承此類

    # Adapters
    DarkThemeTerminalAdapter    彩色 console（深色終端）
    LightThemeTerminalAdapter   彩色 console（淺色終端）
    FileAdapter                 thread-safe 本機日誌檔案
    DarkThemeTkinterAdapter     Tkinter Text widget（深色主題）
    LightThemeTkinterAdapter    Tkinter Text widget（淺色主題）
    DarkThemeTkLabelAdapter     Tkinter tk.Label（深色主題）
    LightThemeTkLabelAdapter    Tkinter tk.Label（淺色主題）
    DarkThemeTtkLabelAdapter    Tkinter ttk.Label（深色主題）
    LightThemeTtkLabelAdapter   Tkinter ttk.Label（淺色主題）
    LocalHTTPAdapter           本機/遠端 HTTP JSON POST（MVP）
    QueuedSocketAdapter        非阻塞 queue + worker socket 骨架
    HTMLAdapter                 HTML 輸出 stub
    HTTPAdapter                 HTTP 遠端輸出 stub
    DBAdapter                   資料庫輸出 stub
    WebsocketAdapter            WebSocket 輸出 stub

    # Types
    LogLevelLiteral     等級字串的 Literal 型別
    LevelOrder          等級 → 數值對應字典
"""

from .base.levels import LogLevelLiteral, LevelOrder
from .base.LoggerAdapterBase import LoggerAdapterBase
from .base.LoggerBase import LoggerBase
from .adapters import (
    AbstractTerminalAdapterBase,
    DarkThemeTerminalAdapter,
    LightThemeTerminalAdapter,
    FileAdapter,
    AbstractTkinterAdapterBase,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
    TkLabelAdapter,
    DarkThemeTkLabelAdapter,
    LightThemeTkLabelAdapter,
    TtkLabelAdapter,
    DarkThemeTtkLabelAdapter,
    LightThemeTtkLabelAdapter,
    LocalHTTPAdapter,
    QueuedSocketAdapter,
    HTMLAdapter,
    HTTPAdapter,
    DBAdapter,
    WebsocketAdapter,
)
from .SingletonSystemLogger import SingletonSystemLogger

__all__ = [
    # types
    "LogLevelLiteral",
    "LevelOrder",
    # base classes
    "LoggerAdapterBase",
    "LoggerBase",
    # adapters (abstract)
    "AbstractTerminalAdapterBase",
    "AbstractTkinterAdapterBase",
    "TkLabelAdapter",
    "TtkLabelAdapter",
    # adapters (concrete — terminal)
    "DarkThemeTerminalAdapter",
    "LightThemeTerminalAdapter",
    # adapters (concrete — file)
    "FileAdapter",
    # adapters (concrete — tkinter Text)
    "DarkThemeTkinterAdapter",
    "LightThemeTkinterAdapter",
    # adapters (concrete — tk.Label)
    "DarkThemeTkLabelAdapter",
    "LightThemeTkLabelAdapter",
    # adapters (concrete — ttk.Label)
    "DarkThemeTtkLabelAdapter",
    "LightThemeTtkLabelAdapter",
    # adapters (concrete — remote)
    "LocalHTTPAdapter",
    "QueuedSocketAdapter",
    # adapters (stub)
    "HTMLAdapter",
    "HTTPAdapter",
    "DBAdapter",
    "WebsocketAdapter",
    # logger
    "SingletonSystemLogger",
]
