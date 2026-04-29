import os
from datetime import datetime
from typing import List

from colorama import init as colorama_init
colorama_init()

from .LoggerAdapterBase import LoggerAdapterBase
from .levels import LogLevelLiteral, LevelOrder
_CURRENT_RUN_MODE = os.environ.get("RUN_MODE", "DEBUG").upper()
_GLOBAL_MIN_LEVEL = NONE


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

    def _initialize_manager(self) -> None:
        self._enabled: bool = True
        self._adapters: List[LoggerAdapterBase] = []
        self._max_level_len: int = max(len(lvl) for lvl in LevelOrder)

    # --- Adapter 管理 ---------------------------------------------------------

    def register_adapter(self, adapter: LoggerAdapterBase) -> None:
        """新增一個輸出 adapter。"""
        self._adapters.append(adapter)

    def unregister_adapter(self, adapter: LoggerAdapterBase) -> None:
        """移除指定 adapter；若不存在則靜默忽略。"""
        try:
            self._adapters.remove(adapter)
        except ValueError:
            pass

    def clear_adapters(self) -> None:
        """移除所有已註冊的 adapter。"""
        self._adapters.clear()

    # --- 全域開關 -------------------------------------------------------------

    def enable_broadcast_msg(self) -> None:
        """重新啟用 log 廣播。"""
        self._enabled = True

    def disable_broadcast_msg(self) -> None:
        """暫時停用 log 廣播（不影響 adapter 設定）。"""
        self._enabled = False

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

        if level == "HIGHLIGHT":
            formatted = f"\n[{timestamp}] [{padded_level}]: 🚀🚀🚀 {message} 🚀🚀🚀"
        elif shine:
            formatted = f"[{timestamp}] [{padded_level}]: ✨ {message} ✨"
        else:
            formatted = f"[{timestamp}] [{padded_level}]: {message}"

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
