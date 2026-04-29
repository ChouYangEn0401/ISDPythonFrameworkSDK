from pathlib import Path
from typing import Optional

from isd_py_framework_sdk.base.Singleton import SingletonMetaclass
from isd_py_framework_sdk.message_logger.base.levels import LogLevelLiteral
from isd_py_framework_sdk.message_logger.base.LoggerBase import LoggerBase
from isd_py_framework_sdk.message_logger.adapters import (
    LoggerAdapterBase,
    TkinterAdapter,
)


class SingletonSystemLogger(LoggerBase, metaclass=SingletonMetaclass):

    def _initialize_manager(self) -> None: ...

    # --- Adapter 管理 ---------------------------------------------------------

    def register_adapter(self, adapter: LoggerAdapterBase) -> None:
        """新增一個輸出 adapter。"""
        ...

    def unregister_adapter(self, adapter: LoggerAdapterBase) -> None:
        """移除指定 adapter；若不存在則靜默忽略。"""
        ...

    def clear_adapters(self) -> None:
        """移除所有已註冊的 adapter。"""
        ...

    # --- 全域開關 -------------------------------------------------------------

    def enable_broadcast_msg(self) -> None:
        """重新啟用 log 廣播。"""
        ...

    def disable_broadcast_msg(self) -> None:
        """暫時停用 log 廣播（不影響 adapter 設定）。"""
        ...

    # --- 核心 log 方法 --------------------------------------------------------

    def shiny_log(self, message: str, level: LogLevelLiteral = "INFO") -> None:
        """以 ✨ 裝飾輸出；adapter 端會同時套用粗體 / 高亮樣式。"""
        ...

    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False) -> None:
        """
        主要 log 方法。格式化後 fan-out 至所有已註冊的 adapter。
        各 adapter 依自身 level_filter 決定是否輸出。
        """
        ...

    # --- 快捷方法 -------------------------------------------------------------

    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def checkpoint(self, msg: str) -> None: ...
    def success(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def critical(self, msg: str) -> None: ...
    def highlight(self, msg: str) -> None: ...
