import os
from datetime import datetime
from typing import List

from colorama import init as colorama_init
colorama_init()

from .LoggerAdapterBase import LoggerAdapterBase
from .levels import LogLevelLiteral, LevelOrder

# 全域 RUN_MODE：控制最低可通過的等級門檻
# DEBUG   → 全部等級通過（預設）
# DISPLAY → INFO 以上
# RUN     → 僅 ERROR 以上（生產模式）
_RUN_MODE_FILTER: dict[str, str] = {
    "DEBUG":   "DEBUG",
    "DISPLAY": "INFO",
    "RUN":     "ERROR",
}
_CURRENT_RUN_MODE = os.environ.get("RUN_MODE", "DEBUG").upper()
_GLOBAL_MIN_LEVEL = _RUN_MODE_FILTER.get(_CURRENT_RUN_MODE, "DEBUG")


class LoggerBase:
    """
        Logger 核心基底類別。

        負責：
            - 格式化訊息（timestamp、level padding、HIGHLIGHT / shiny 裝飾）
            - 全域啟用 / 停用開關
            - 管理已註冊的 adapter 清單
            - fan-out：廣播給所有 adapter（各 adapter 自行套用自己的 level_filter）

        全域 RUN_MODE 過濾（環境變數 RUN_MODE，讀取一次，執行期固定）：
            DEBUG   — 全部等級通過（預設）
            DISPLAY — INFO 以上通過
            RUN     — 僅 ERROR 以上通過
    """

    @property
    def adapters(self) -> List[LoggerAdapterBase]:
        """目前已註冊的 adapter 清單（只讀）。"""
        return self._adapters.copy()

    def _initialize_manager(self) -> None:
        self._enabled: bool = True
        self._adapters: List[LoggerAdapterBase] = []
        self._max_level_len: int = max(len(lvl) for lvl in LevelOrder)
        self._shift_amount = 0

    # --- Adapter 管理 ---------------------------------------------------------

    def register_adapter(self, adapter: LoggerAdapterBase) -> None:
        """新增一個輸出 adapter。"""
        self._adapters.append(adapter)

    def add_adapter(self, adapter: LoggerAdapterBase) -> LoggerAdapterBase:
        """新增一個輸出 adapter，並回傳該 adapter 方便呼叫端保留參考。"""
        self.register_adapter(adapter)
        return adapter

    def unregister_adapter(self, adapter: LoggerAdapterBase) -> None:
        """移除指定 adapter；若不存在則靜默忽略。"""
        try:
            self._adapters.remove(adapter)
        except ValueError:
            pass

    remove_adapter = unregister_adapter

    def clear_adapters(self) -> None:
        """移除所有已註冊的 adapter。"""
        self._adapters.clear()

    # --- 全域開關 -------------------------------------------------------------

    def enable_broadcast_msg(self) -> None:
        """重新啟用 log 廣播。"""
        self._enabled = True

    enable = enable_broadcast_msg

    def disable_broadcast_msg(self) -> None:
        """暫時停用 log 廣播（不影響 adapter 設定）。"""
        self._enabled = False

    disable = disable_broadcast_msg

    # --- 核心 log 方法 --------------------------------------------------------

    def shiny_log(self, message: str, level: LogLevelLiteral = "INFO") -> None:
        """以 ✨ 裝飾輸出；adapter 端會同時套用粗體/高亮樣式。"""
        self.log(message, level, shine=True)

    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False) -> None:
        """
        主要 log 方法。

        格式化訊息後 fan-out 至所有已註冊的 adapter，
        各 adapter 依自身 level_filter 決定是否實際輸出。
        """
        if not self._enabled:
            return

        # --- Normalize & Validate Level ---
        level = level.upper()
        if level not in LevelOrder:
            raise ValueError(f"未知的等級：'{level}'。可用等級：{list(LevelOrder.keys())}")

        # --- Global RUN_MODE Filter ---
        if LevelOrder[level] < LevelOrder[_GLOBAL_MIN_LEVEL]:
            return

        # --- Message Formatting ---
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        padded_level = level.ljust(self._max_level_len)
        indent = "\t" * self._shift_amount

        if level == "HIGHLIGHT":
            formatted = f"\n{indent}[{timestamp}] [{padded_level}]: 🚀🚀🚀 {message} 🚀🚀🚀"
        elif shine:
            formatted = f"{indent}[{timestamp}] [{padded_level}]: ✨ {message} ✨"
        else:
            formatted = f"{indent}[{timestamp}] [{padded_level}]: {message}"

        # --- Fan-out to All Adapters ---
        for adapter in self._adapters:
            adapter.broadcast(level, formatted, shine)

    # --- 快捷方法 -------------------------------------------------------------

    def debug(self, msg: str) -> None:      self.log(msg, "DEBUG")
    def info(self, msg: str) -> None:       self.log(msg, "INFO")
    def checkpoint(self, msg: str) -> None: self.log(msg, "CHECKPOINT")
    def success(self, msg: str) -> None:    self.log(msg, "SUCCESS")
    def warning(self, msg: str) -> None:    self.log(msg, "WARNING")
    def error(self, msg: str) -> None:      self.log(msg, "ERROR")
    def critical(self, msg: str) -> None:   self.log(msg, "CRITICAL")
    def highlight(self, msg: str) -> None:  self.log(msg, "HIGHLIGHT")

    # --- Flush ---------------------------------------------------------------

    def flush_all(self) -> None:
        """Flush 所有已註冊的 adapter（例如 FileAdapter flush 至磁碟、TkinterAdapter 更新 widget）。"""
        for adapter in self._adapters:
            adapter.flush()

    def flush(self) -> None:
        """Alias for flush_all()。"""
        self.flush_all()

    # --- Shrift Head ---------------------------------------------------------

    def shift(self) -> None:
        """暫時保留接口，未來可用於實現 log 分頁或分段功能。"""
        self._shift_amount += 1
    
    def unshift(self) -> None:
        """暫時保留接口，未來可用於實現 log 分頁或分段功能。"""
        self._shift_amount -= 1
        if self._shift_amount < 0:
            self._shift_amount = 0

