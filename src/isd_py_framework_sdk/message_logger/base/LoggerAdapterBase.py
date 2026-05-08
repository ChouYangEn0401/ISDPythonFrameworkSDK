from abc import ABC, abstractmethod
from typing import Any

from .levels import LevelOrder, LogLevelLiteral


class LoggerAdapterBase(ABC):
    """
        所有輸出 adapter 的抽象基底類別。

        子類只需實作 broadcast()，並在建構時傳入 level_filter 設定最低顯示等級。
        level_filter 之上（含）的訊息才會被輸出；低於此等級的訊息會被靜默略過。
    """

    def __init__(
        self,
        level_filter: LogLevelLiteral | str = "INFO",
        *args: Any,
        **kwargs: Any,
    ):
        legacy_level_filter = kwargs.pop("LEVEL_FILTER", None)
        if legacy_level_filter is not None:
            if level_filter != "INFO":
                raise TypeError("Use either level_filter or LEVEL_FILTER, not both.")
            level_filter = legacy_level_filter

        self.level_filter = self.normalize_level(level_filter)
        self._have_level(self.level_filter, b_stop_when_error=True)

    # --- Core Method ---------------------------------------------------------

    @abstractmethod
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        """接收格式化後的訊息並輸出至目標媒介。"""
        pass

    def set_filtered_level(self, level: LogLevelLiteral) -> None:
        """動態變更此 adapter 的最低顯示等級。"""
        level = self.normalize_level(level)
        if self._have_level(level, b_stop_when_error=True):
            self.level_filter = level

    set_level_filter = set_filtered_level

    def flush(self) -> None:
        """Flush any buffered output. Override in adapters that buffer output (e.g. FileAdapter, TkinterAdapter)."""
        pass

    # --- Utility -------------------------------------------------------------

    @staticmethod
    def help() -> None:
        """印出所有可用等級與對應數值。"""
        print("等級由低到高：DEBUG < INFO < CHECKPOINT < SUCCESS < WARNING < ERROR < CRITICAL < HIGHLIGHT")
        for key, value in LevelOrder.items():
            print(f"  {key:<12} = {value}")

    @staticmethod
    def normalize_level(level: str) -> str:
        return level.upper()

    level_formator = normalize_level

    @staticmethod
    def _have_level(level: str, b_stop_when_error: bool = False) -> bool:
        if level in LevelOrder:
            return True
        if b_stop_when_error:
            raise ValueError(f"未知的等級：'{level}'。可用等級：{list(LevelOrder.keys())}")
        return False

    def _pass_filter(self, level: str) -> bool:
        """True 代表此等級可以通過並輸出（>= level_filter）。"""
        level = self.normalize_level(level)
        self._have_level(level, b_stop_when_error=True)
        return LevelOrder[level] >= LevelOrder[self.level_filter]

    def should_emit(self, level: str) -> bool:
        """True 代表此等級可以通過此 adapter 的 level_filter。"""
        return self._pass_filter(level)
