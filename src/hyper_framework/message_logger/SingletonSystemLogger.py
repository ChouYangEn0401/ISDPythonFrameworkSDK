import os
from datetime import datetime
from typing import List, Literal

from colorama import init as colorama_init
from hyper_framework.base.Singleton import SingletonMetaclass
from hyper_framework.message_logger._sinks import LogSink, TerminalSink, FileSink, TkinterSink

# 初始化 colorama（讓 Windows 也能顯示 ANSI 色碼）
colorama_init()
_CURRENT_RUN_MODE = os.environ.get("RUN_MODE", "DEBUG")


class SingletonSystemLogger(metaclass=SingletonMetaclass):
    LogLevelLiteral = Literal[
        "DEBUG", "INFO",
        "CHECKPOINT", "SUCCESS", "WARNING",
        "ERROR", "CRITICAL",
        "HIGHLIGHT"
    ]

    """
    單例 Logger，負責格式化與等級過濾，再將訊息 fan-out 至所有已註冊的 sink。

    輸出目標（sink）可自由組合：
        TerminalSink  — 彩色 console 輸出
        FileSink      — 本機檔案輸出
        TkinterSink   — Tkinter Text widget 輸出

    每個 sink 持有自己的最低顯示等級，彼此獨立互不干擾。

    Log Levels（由低到高）：
        DEBUG:      用於詳細調試資訊，開發時用，平時一般不顯示。
        INFO:       重要的正常運行訊息，例如系統啟動、完成某任務。
        CHECKPOINT: 流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯。
        SUCCESS:    特殊的成功訊息，表示某個操作成功完成，比 INFO 更突出成功狀態。
        WARNING:    警告訊息，提示可能有問題但不影響運行。
        ERROR:      錯誤訊息，表示操作失敗或重要錯誤，需要關注。
        CRITICAL:   致命錯誤，系統崩潰或無法繼續執行，需要立即處理。
        HIGHLIGHT:  超醒目提示。

    環境變數：
        RUN_MODE=DEBUG    （預設）全部等級通過
        RUN_MODE=DISPLAY  INFO 以上通過
        RUN_MODE=RUN      僅 ERROR 通過
        CONSOLE_BG=dark|light  調整 TerminalSink 顏色主題
    """

    def _initialize_manager(self):
        self._enabled = True
        self._sinks: List[LogSink] = []

        self._level_order = {
            "DEBUG":      10,
            "INFO":       20,
            "CHECKPOINT": 22,
            "SUCCESS":    25,
            "WARNING":    30,
            "ERROR":      40,
            "CRITICAL":   50,
            "HIGHLIGHT":  60,
        }
        self._max_level_len = max(len(lvl) for lvl in self._level_order)

    # ─── Sink 管理 ──────────────────────────────────────────────────────────

    def register_sink(self, sink: LogSink) -> None:
        """新增一個輸出 sink（TerminalSink / FileSink / TkinterSink / 自訂）。"""
        self._sinks.append(sink)

    def unregister_sink(self, sink: LogSink) -> None:
        """移除指定 sink。"""
        self._sinks.remove(sink)

    def clear_sinks(self) -> None:
        """移除所有已註冊的 sinks。"""
        self._sinks.clear()

    # ─── 全域開關 ────────────────────────────────────────────────────────────

    def enable(self) -> None:
        """允許 logger 輸出。"""
        self._enabled = True

    def disable(self) -> None:
        """暫停 logger 輸出（不影響 sink 設定）。"""
        self._enabled = False

    # ─── 工具 ────────────────────────────────────────────────────────────────

    @staticmethod
    def help() -> None:
        """印出所有可用的 log 等級與對應數值。"""
        print("訊息順序：DEBUG < INFO < CHECKPOINT < SUCCESS < WARNING < ERROR < CRITICAL < HIGHLIGHT")
        for key, val in SingletonSystemLogger()._level_order.items():
            print(f"  {key:<12} level={val}")

    # ─── 核心 log 方法 ───────────────────────────────────────────────────────

    def shiny_log(self, message: str, level: LogLevelLiteral = "INFO") -> None:
        """以 ✨ 裝飾輸出（TerminalSink 會同時加亮顏色）。"""
        self.log(message, level, shine=True)

    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False) -> None:
        """
        主要 log 方法。格式化訊息後，依各 sink 的最低等級設定進行 fan-out 輸出。

        Log Levels（由低到高）：
            DEBUG / INFO / CHECKPOINT / SUCCESS / WARNING / ERROR / CRITICAL / HIGHLIGHT
        """
        if not self._enabled:
            return

        level = level.upper()
        if level not in self._level_order:
            raise ValueError(f"未知的等級：{level}")

        if _CURRENT_RUN_MODE == "RUN" and level != "ERROR":
            return

        if level == "INFO" and _CURRENT_RUN_MODE not in ["DEBUG", "DISPLAY"]:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        padded = level.ljust(self._max_level_len)

        if level == "HIGHLIGHT":
            formatted = f"\n[{timestamp}] [{padded}]: 🚀🚀🚀 {message} 🚀🚀🚀"
        elif shine:
            formatted = f"[{timestamp}] [{padded}]: ✨ {message} ✨"
        else:
            formatted = f"[{timestamp}] [{padded}]: {message}"

        for sink in self._sinks:
            if sink.allow(level, self._level_order):
                sink.emit(formatted, level, shine=shine)

    # ─── 快捷方法 ────────────────────────────────────────────────────────────

    def debug(self, msg: str): self.log(msg, "DEBUG")
    def info(self, msg: str): self.log(msg, "INFO")
    def checkpoint(self, msg: str): self.log(msg, "CHECKPOINT")
    def success(self, msg: str): self.log(msg, "SUCCESS")
    def warning(self, msg: str): self.log(msg, "WARNING")
    def error(self, msg: str): self.log(msg, "ERROR")
    def critical(self, msg: str): self.log(msg, "CRITICAL")
    def highlight(self, msg: str): self.log(msg, "HIGHLIGHT")


# ─── 測試函式 ─────────────────────────────────────────────────────────────────

def test_logger_basic_flow():
    """
    基礎測試：SingletonSystemLogger + sink 組合

    測試流程：
    1. 只有 FileSink（min_level=WARNING），確認 WARNING 以下不寫入
    2. 加入 TerminalSink（min_level=DEBUG），全部等級顯示
    3. TerminalSink 改為 min_level=INFO，DEBUG 不顯示
    """
    logger = SingletonSystemLogger()
    logger.clear_sinks()

    file_sink = FileSink("test_logger.log", min_level="WARNING")
    logger.register_sink(file_sink)

    print("=== [階段 1] FileSink min_level=WARNING ===")
    logger.info("INFO 訊息，預期不輸出")
    logger.debug("DEBUG 訊息，預期不輸出")
    logger.checkpoint("CHECKPOINT 訊息，預期不輸出")
    logger.success("SUCCESS 訊息，預期不輸出")
    logger.warning("WARNING 訊息，預期輸出至檔案")
    logger.error("ERROR 訊息，預期輸出至檔案")
    logger.critical("CRITICAL 訊息，預期輸出至檔案")
    print("請檢查 test_logger.log 確認只有 WARNING / ERROR / CRITICAL。")

    print("\n=== [階段 2] 再加入 TerminalSink min_level=DEBUG ===")
    terminal_sink = TerminalSink(min_level="DEBUG")
    logger.register_sink(terminal_sink)

    logger.debug("Debug 訊息，預期顯示在 terminal")
    logger.info("Info 訊息，預期顯示在 terminal")
    logger.checkpoint("Checkpoint 訊息")
    logger.success("Success 訊息")
    logger.warning("Warning 訊息，terminal + file")
    logger.error("Error 訊息，terminal + file")
    logger.critical("Critical 訊息，terminal + file")

    print("\n=== [階段 3] TerminalSink 改 min_level=INFO ===")
    terminal_sink.set_min_level("INFO")

    logger.debug("Debug 訊息，預期不顯示")
    logger.info("Info 訊息，預期顯示")
    logger.warning("Warning 訊息，預期顯示")
    logger.highlight("Highlight 訊息，預期顯示")

    print("\n✅ 測試完成，請確認 console 與 test_logger.log 中輸出結果。")


def test_logger_level_order_and_aliases():
    """
    等級排序與顏色測試：
    - 確認 checkpoint 層級正確排序在 INFO 和 SUCCESS 之間
    - 全等級輸出以驗證排序與顏色
    """
    logger = SingletonSystemLogger()
    logger.clear_sinks()
    logger.register_sink(TerminalSink(min_level="DEBUG"))

    print("=== 全等級輸出（確認顏色與排序）===")
    logger.debug("Debug 訊息")
    logger.info("Info 訊息")
    logger.checkpoint("Checkpoint 訊息")
    logger.success("Success 訊息")
    logger.warning("Warning 訊息")
    logger.error("Error 訊息")
    logger.critical("Critical 訊息")
    logger.highlight("Highlight 訊息")
    logger.shiny_log("Shiny 訊息（✨ + 亮色）", "SUCCESS")

    print("\n✅ 等級排序與顏色測試完成")


def test_logger_file_output_content():
    """
    測試 FileSink 輸出內容格式與寫入：
    - 輸出多種等級訊息至指定檔案
    - 請手動確認檔案內容格式正確
    """
    log_file = "test_file_output.log"
    logger = SingletonSystemLogger()
    logger.clear_sinks()
    logger.register_sink(FileSink(log_file, min_level="DEBUG"))

    messages = [
        ("info",       "Info 訊息"),
        ("debug",      "Debug 訊息"),
        ("checkpoint", "Checkpoint 訊息"),
        ("success",    "Success 訊息"),
        ("warning",    "Warning 訊息"),
        ("error",      "Error 訊息"),
        ("critical",   "Critical 訊息"),
    ]

    for level_name, msg in messages:
        getattr(logger, level_name)(msg)

    print(f"✅ 訊息已輸出至 {log_file}，請手動檢查內容格式。")


def tkinter_gui_text_testing():
    import tkinter as tk
    from tkinter import ttk

    class LoggerGUI(tk.Tk):
        LEVELS = ["ALL", "DEBUG", "INFO", "CHECKPOINT", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

        def __init__(self):
            super().__init__()
            self.title("Logger GUI 測試")
            self.geometry("800x400")

            self.text_widget = tk.Text(self, wrap="word", height=20, width=100, state=tk.NORMAL)
            self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self.tk_sink = TkinterSink(self.text_widget, min_level="DEBUG")

            self.logger = SingletonSystemLogger()
            self.logger.clear_sinks()
            self.logger.register_sink(self.tk_sink)

            self.messages = [
                ("INFO",       "這是 INFO 訊息"),
                ("DEBUG",      "這是 DEBUG 訊息"),
                ("CHECKPOINT", "這是 CHECKPOINT 訊息"),
                ("SUCCESS",    "這是 SUCCESS 訊息"),
                ("WARNING",    "這是 WARNING 訊息"),
                ("ERROR",      "這是 ERROR 訊息"),
                ("CRITICAL",   "這是 CRITICAL 訊息"),
                ("HIGHLIGHT",  "這是 HIGHLIGHT 訊息"),
            ]

            control_frame = ttk.Frame(self)
            control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

            ttk.Label(control_frame, text="設定顯示最低等級：").pack(side=tk.LEFT)
            self.min_level_var = tk.StringVar(value="ALL")
            level_combo = ttk.Combobox(
                control_frame, textvariable=self.min_level_var,
                values=self.LEVELS, state="readonly", width=12,
            )
            level_combo.pack(side=tk.LEFT, padx=5)
            level_combo.bind("<<ComboboxSelected>>", self.on_level_change)

            self.update_text("ALL")

        def on_level_change(self, event=None):
            self.update_text(self.min_level_var.get())

        def update_text(self, min_level):
            level_priority = {level: i for i, level in enumerate(self.LEVELS)}
            min_priority = level_priority[min_level]

            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete("1.0", tk.END)

            for level, msg in self.messages:
                if min_level == "ALL" or level_priority[level] >= min_priority:
                    self.text_widget.insert(tk.END, f"[{level}] {msg}\n", level)

            self.text_widget.config(state=tk.DISABLED)

    app = LoggerGUI()
    app.mainloop()


if __name__ == "__main__":
    test_logger_level_order_and_aliases()
    test_logger_basic_flow()
    # test_logger_file_output_content()
    # tkinter_gui_text_testing()
