from abc import ABC, abstractmethod
import os
from datetime import datetime
from typing import Optional, Literal, TYPE_CHECKING

from colorama import Fore, Style, init as colorama_init
from personal_experiment.enum import LogLevelLiteral

# 初始化 colorama（讓 Windows 也能顯示 ANSI 色碼）
_CURRENT_RUN_MODE = os.environ.get("RUN_MODE", "DEBUG")
if TYPE_CHECKING:
    from tkinter import Text


class LoggerBase():
    """
    專業的單例 SingletonSystemLogger，支援等級過濾、對齊、顏色與多種輸出模式。

    Log Levels（由低到高）：
        DEBUG:        用於詳細調試資訊，開發時用，平時一般不顯示。
        INFO:         重要的正常運行訊息，例如系統啟動、完成某任務。
        CHECKPOINT:   流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯。
        SUCCESS:      特殊的成功訊息，表示某個操作成功完成，比 INFO 更突出成功狀態。
        WARNING:      警告訊息，提示可能有問題但不影響運行。
        ERROR:        錯誤訊息，表示操作失敗或重要錯誤，需要關注。
        CRITICAL:     致命錯誤，系統崩潰或無法繼續執行，需要立即處理。
        HIGHLIGHT:   超醒目提示。
    """

    def _initialize_manager(self, adapters: Optional[list] = None):
        self._enabled = True
        # self._min_level = "DEBUG"
        self._max_level_len = max(len(lvl) for lvl in LogLevelLiteral)
        self._adapters = adapters if adapters is not None else []
        colorama_init()

    # ------------------- 可設定交互與否的方法 --------------------

    def enable_broadcast_msg(self): self._enabled = True
    def disable_broadcast_msg(self): self._enabled = False

    # ------------------- 核心 log 方法 --------------------

    def shiny_log(self, message: str, level: LogLevelLiteral = "INFO"):
        """ ShinyMode=True, Log """
        self.log(message, level, shine=True)

    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False):
        """
            Log Text
            Log Levels（由低到高）：
                DEBUG:        用於詳細調試資訊，開發時用，平時一般不顯示。
                INFO:         重要的正常運行訊息，例如系統啟動、完成某任務。
                CHECKPOINT:   流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯。
                SUCCESS:      特殊的成功訊息，表示某個操作成功完成，比 INFO 更突出成功狀態。
                WARNING:      警告訊息，提示可能有問題但不影響運行。
                ERROR:        錯誤訊息，表示操作失敗或重要錯誤，需要關注。
                CRITICAL:     致命錯誤，系統崩潰或無法繼續執行，需要立即處理。
                HIGHLIGHT:   超醒目提示。
            ShinyMode=False
        """
        ## Check Runnable
        if not self._enabled:
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

        ## Broadcast Message To Adapters
        for adapter in self._adapters:
            adapter.broadcast(level, formatted, shine)
    

    # ------------------- 快捷方法 --------------------

    def debug(self, msg: str): self.log(msg, "DEBUG")
    def info(self, msg: str): self.log(msg, "INFO")
    def checkpoint(self, msg: str): self.log(msg, "CHECKPOINT")
    def success(self, msg: str): self.log(msg, "SUCCESS")
    def warning(self, msg: str): self.log(msg, "WARNING")
    def error(self, msg: str): self.log(msg, "ERROR")
    def critical(self, msg: str): self.log(msg, "CRITICAL")
    def highlight(self, msg: str): self.log(msg, "HIGHLIGHT")

