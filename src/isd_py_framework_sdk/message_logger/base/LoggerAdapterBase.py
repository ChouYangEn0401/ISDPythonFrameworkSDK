from abc import ABC, abstractmethod

from .levels import LevelOrder, LogLevelLiteral


class LoggerAdapterBase(ABC):
    """
        所有輸出 adapter 的抽象基底類別。

        子類只需實作 broadcast()，並在建構時傳入 LEVEL_FILTER 設定最低顯示等級。
        level_filter 之上（含）的訊息才會被輸出；低於此等級的訊息會被靜默略過。
    """

    def __init__(self, LEVEL_FILTER: LogLevelLiteral, *args, **kwargs):
        self.level_filter = self.level_formator(LEVEL_FILTER)

    # --- Core Method ---------------------------------------------------------

    @abstractmethod
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        """接收格式化後的訊息並輸出至目標媒介。"""
        pass

    def set_filtered_level(self, level: LogLevelLiteral) -> None:
        """動態變更此 adapter 的最低顯示等級。"""
        level = self.level_formator(level)
        if self._have_level(level, b_stop_when_error=True):
            self.level_filter = level

    # --- Utility -------------------------------------------------------------

    @staticmethod
    def help() -> None:
        """印出所有可用等級與對應數值。"""
        print("等級由低到高：DEBUG < INFO < CHECKPOINT < SUCCESS < WARNING < ERROR < CRITICAL < HIGHLIGHT")
        for key, value in LevelOrder.items():
            print(f"  {key:<12} = {value}")

    @staticmethod
    def level_formator(level: str) -> str:
        return level.upper()

    @staticmethod
    def _have_level(level: str, b_stop_when_error: bool = False) -> bool:
        if level in LevelOrder:
            return True
        if b_stop_when_error:
            raise ValueError(f"未知的等級：'{level}'。可用等級：{list(LevelOrder.keys())}")
        return False

    def _pass_filter(self, level: str) -> bool:
        """True 代表此等級可以通過並輸出（>= level_filter）。"""
        return LevelOrder[level] >= LevelOrder[self.level_filter]
