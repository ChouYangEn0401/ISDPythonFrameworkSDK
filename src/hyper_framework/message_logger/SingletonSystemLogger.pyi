from hyper_framework.base.Singleton import SingletonMetaclass as SingletonMetaclass
from hyper_framework.message_logger._sinks import LogSink as LogSink
from hyper_framework.message_logger._sinks import TerminalSink as TerminalSink
from hyper_framework.message_logger._sinks import FileSink as FileSink
from hyper_framework.message_logger._sinks import TkinterSink as TkinterSink
from typing import List, Literal


class SingletonSystemLogger(metaclass=SingletonMetaclass):
    LogLevelLiteral = Literal[
        "DEBUG", "INFO",
        "CHECKPOINT", "SUCCESS", "WARNING",
        "ERROR", "CRITICAL",
        "HIGHLIGHT"
    ]

    """
    單例 Logger，負責格式化與等級過濾，再將訊息 fan-out 至所有已註冊的 sink。

    Log Levels（由低到高）：
        DEBUG / INFO / CHECKPOINT / SUCCESS / WARNING / ERROR / CRITICAL / HIGHLIGHT

    環境變數：
        RUN_MODE=DEBUG|DISPLAY|RUN
        CONSOLE_BG=dark|light
    """

    _sinks: List[LogSink]

    # ── Sink 管理 ─────────────────────────────────────
    def register_sink(self, sink: LogSink) -> None:
        """新增一個輸出 sink。"""
        ...
    def unregister_sink(self, sink: LogSink) -> None:
        """移除指定 sink。"""
        ...
    def clear_sinks(self) -> None:
        """移除所有 sinks。"""
        ...

    # ── 全域開關 ──────────────────────────────────────
    def enable(self) -> None: ...
    def disable(self) -> None: ...

    # ── 工具 ──────────────────────────────────────────
    @staticmethod
    def help() -> None: ...

    # ── 核心 log 方法 ─────────────────────────────────
    def shiny_log(self, message: str, level: LogLevelLiteral = "INFO") -> None:
        """以 ✨ 裝飾輸出。"""
        ...
    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False) -> None:
        """主要 log 方法，格式化後 fan-out 至所有允許此等級的 sinks。"""
        ...

    # ── 快捷方法 ──────────────────────────────────────
    def debug(self, msg: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def checkpoint(self, msg: str) -> None: ...
    def success(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def critical(self, msg: str) -> None: ...
    def highlight(self, msg: str) -> None: ...


def test_logger_basic_flow() -> None: ...
def test_logger_level_order_and_aliases() -> None: ...
def test_logger_file_output_content() -> None: ...
def tkinter_gui_text_testing() -> None: ...
