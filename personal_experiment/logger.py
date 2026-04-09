import os
from datetime import datetime
from typing import List

from colorama import init as colorama_init
from personal_experiment.levels import LogLevelLiteral, LevelOrder

colorama_init()
_CURRENT_RUN_MODE = os.environ.get("RUN_MODE", "DEBUG")


class LoggerBase:
    """
        Logger 核心基底類別。

        負責：
            - 格式化訊息（timestamp、level padding、HIGHLIGHT / shiny 裝飾）
            - 全域啟用/停用開關
            - 管理已註冊的 adapter 清單
            - fan-out：廣播給所有 adapter（各 adapter 自行過濾）

        全域 RUN_MODE 過濾（環境變數 RUN_MODE）：
            DEBUG   — 全部等級通過（預設）
            DISPLAY — INFO 以上通過
            RUN     — 僅 ERROR 通過

        等級過濾由各 adapter 透過 level_filter 個別控制。
    """

    def _initialize_manager(self):
        self._enabled = True
        self._adapters: List = []
        # LevelOrder 是普通 dict，可安全迭代（Literal 型別在 runtime 無法迭代）
        self._max_level_len = max(len(lvl) for lvl in LevelOrder)

    # --- Adapter 管理 ---------------------------------------------------------

    def register_adapter(self, adapter) -> None:
        """新增一個輸出 adapter。"""
        self._adapters.append(adapter)

    def unregister_adapter(self, adapter) -> None:
        """移除指定 adapter。"""
        self._adapters.remove(adapter)

    def clear_adapters(self) -> None:
        """移除所有已註冊的 adapters。"""
        self._adapters.clear()

    # --- 全域開關 -------------------------------------------------------------

    def enable_broadcast_msg(self): self._enabled = True
    def disable_broadcast_msg(self): self._enabled = False

    # --- 核心 log 方法 --------------------------------------------------------

    def shiny_log(self, message: str, level: LogLevelLiteral = "INFO"):
        """以 ✨ 裝飾輸出（adapter 端會同時加亮顏色）。"""
        self.log(message, level, shine=True)

    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False):
        """
            主要 log 方法。格式化後 fan-out 至所有已註冊的 adapters。
            各 adapter 依自身 level_filter 決定是否輸出。
        """
        if not self._enabled:
            return

        ## Normalize & Validate Level
        level = level.upper()
        if level not in LevelOrder:
            raise ValueError(f"未知的等級：{level}")

        ## Global RUN_MODE Filter
        if _CURRENT_RUN_MODE == "RUN" and level != "ERROR":
            return
        if level == "INFO" and _CURRENT_RUN_MODE not in ["DEBUG", "DISPLAY"]:
            return

        ## Message Preparation
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        padded_level = level.ljust(self._max_level_len)
        if level == "HIGHLIGHT":
            formatted = f"\n[{timestamp}] [{padded_level}]: 🚀🚀🚀 {message} 🚀🚀🚀"
        elif shine:
            formatted = f"[{timestamp}] [{padded_level}]: ✨ {message} ✨"
        else:
            formatted = f"[{timestamp}] [{padded_level}]: {message}"

        ## Broadcast Message To All Adapters
        for adapter in self._adapters:
            adapter.broadcast(level, formatted, shine)

    # --- 快捷方法 -------------------------------------------------------------

    def debug(self, msg: str): self.log(msg, "DEBUG")
    def info(self, msg: str): self.log(msg, "INFO")
    def checkpoint(self, msg: str): self.log(msg, "CHECKPOINT")
    def success(self, msg: str): self.log(msg, "SUCCESS")
    def warning(self, msg: str): self.log(msg, "WARNING")
    def error(self, msg: str): self.log(msg, "ERROR")
    def critical(self, msg: str): self.log(msg, "CRITICAL")
    def highlight(self, msg: str): self.log(msg, "HIGHLIGHT")
