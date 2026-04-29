from abc import ABC, abstractmethod

from isd_py_framework_sdk.message_logger.base.levels import LevelOrder, LogLevelLiteral

class LoggerAdapterBase(ABC):
    """
        所有輸出 adapter 的抽象基底類別。
        子類只需實作 broadcast()，並在建構時傳入 LEVEL_FILTER 設定最低顯示等級。
    """

    def __init__(self, LEVEL_FILTER: LogLevelLiteral, *args, **kwargs):
        self.level_filter = self.level_formator(LEVEL_FILTER)

    # --- Core Method ---------------------------------------------------------

    @abstractmethod
    def broadcast(self, level: str, formatted: str, shine: bool = False): pass

    def set_filtered_level(self, level: LogLevelLiteral):
        """變更此 adapter 的最低顯示等級。"""
        level = self.level_formator(level)
        if self._have_level(level, b_stop_when_error=True):
            self.level_filter = level

    # --- Utility -------------------------------------------------------------

    @staticmethod
    def help():
        """印出所有可用等級與數值。"""
        print("此訊息順序預期為： DEBUG < INFO < CHECKPOINT < SUCCESS < WARNING < ERROR < CRITICAL")
        for key, item in LevelOrder.items():
            print(key, f"at level {item}.")

    @staticmethod
    def level_formator(level: str) -> str:
        return level.upper()

    @staticmethod
    def _have_level(level: str, b_stop_when_error: bool = False) -> bool:
        if level in LevelOrder:
            return True
        elif b_stop_when_error:
            raise ValueError(f"未知的等級：{level}")
        return False

    def _pass_filter(self, level: str) -> bool:
        """True 代表此等級可以通過並輸出。"""
        # >= 確保設定為 DEBUG 時 DEBUG 本身也能通過
        return LevelOrder[level] >= LevelOrder[self.level_filter]