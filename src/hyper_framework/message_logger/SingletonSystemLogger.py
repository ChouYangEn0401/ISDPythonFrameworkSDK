import os
from datetime import datetime
from typing import Optional, Literal, TYPE_CHECKING

from colorama import Fore, Style, init as colorama_init
from hyper_framework.base.Singleton import SingletonMetaclass

# 初始化 colorama（讓 Windows 也能顯示 ANSI 色碼）
colorama_init()
_CURRENT_RUN_MODE = os.environ.get("RUN_MODE", "DEBUG")

if TYPE_CHECKING:
    from tkinter import Text


class SingletonSystemLogger(metaclass=SingletonMetaclass):
    LogLevelLiteral = Literal[
        "DEBUG", "INFO",
        "CHECKPOINT", "SUCCESS", "WARNING",
        "ERROR", "CRITICAL",
        "HIGHLIGHT"
    ]

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

    def _initialize_manager(self):
        self._min_level = "DEBUG"
        self._output_mode = "console"  # console | file | both
        self._log_file = "app.log"
        self._enabled = True
        self._tk_window: Optional["Text"] = None

        self._level_order = {
            "DEBUG": 10,  # 詳細除錯，開發階段有用，平時不顯示
            "INFO": 20,  # 正常運行狀態、流程資訊
            "CHECKPOINT": 22,  # 流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯
            "SUCCESS": 25,  # 特殊的成功狀態訊息，比 INFO 更突出
            "WARNING": 30,  # 潛在問題、非致命警告
            "ERROR": 40,  # 錯誤，操作失敗需修正
            "CRITICAL": 50,  # 致命錯誤，系統無法正常運作
            "HIGHLIGHT": 60,  # 炫泡的燈光效果？？
        }

        self._tk_colors = {
            "DEBUG": "#0000ff",  # 藍色
            "INFO": "#000000",  # 黑色
            "CHECKPOINT": "#66ffff",  # 淺青
            "SUCCESS": "#228B22",  # 深綠 ForestGreen
            "WARNING": "#C19A6B",  # 焦糖色 Camel
            "ERROR": "#ff0000",  # 紅
            "CRITICAL": "#ff00ff",  # 洋紅
            "HIGHLIGHT": "#ffff33",  # 亮黃
        }

        _console_colors_dark = {
            "INFO": Fore.WHITE,  # 白色，穩重訊息
            "DEBUG": Fore.BLUE,  # 藍色，適合詳細除錯
            "CHECKPOINT": Fore.LIGHTCYAN_EX,  # 淺青色，醒目且專業，和INFO不同
            "SUCCESS": Fore.LIGHTGREEN_EX,  # 淺綠色，成功訊息
            "WARNING": Fore.YELLOW,  # 黃色，警告訊息
            "ERROR": Fore.RED,  # 紅色，錯誤訊息
            "CRITICAL": Fore.MAGENTA,  # 洋紅色，致命錯誤
            "HIGHLIGHT": Fore.LIGHTYELLOW_EX + Style.BRIGHT,  # 搭配明亮黃色 + 強化字體
        }
        _console_colors_light = {
            "DEBUG": Fore.BLUE,  # 藍色仍清晰
            "INFO": Fore.BLACK,  # 黑色適合白底
            "CHECKPOINT": Fore.CYAN,  # 深青色
            "SUCCESS": Fore.GREEN,  # 綠色比亮綠好
            "WARNING": Fore.MAGENTA,  # 用紫色強調警告
            "ERROR": Fore.RED,  # 紅色保留
            "CRITICAL": Fore.MAGENTA,  # 洋紅色
            "HIGHLIGHT": Fore.BLUE + Style.BRIGHT,  # 醒目的亮藍
        }

        # 從環境變數讀取背景主題（預設 dark）
        _console_bg = os.environ.get("CONSOLE_BG", "dark").lower()
        if _console_bg == "light":
            self._level_colors = _console_colors_light
        else:
            self._level_colors = _console_colors_dark

        self._max_level_len = max(len(lvl) for lvl in self._level_order)

    @staticmethod
    def help():
        """ Show The Level For Each Usable Mode """
        print("此訊息順序預期為：DEBUG < INFO < CHECKPOINT < SUCCESS < WARNING < ERROR < CRITICAL")
        for key, item in SingletonSystemLogger()._level_order:
            print(key, f"at level {item}.")

    # ------------------- 可設定方法 --------------------

    def set_min_level(
            self,
            level: LogLevelLiteral
    ):
        """ Set The Lowest Showcase Level """
        if level in self._level_order:
            self._min_level = level

    def set_output_mode(self, mode: Literal["console", "file", "both"]):
        """ Set Message OutPut Mode """
        if mode.lower() in ("console", "file", "both"):
            self._output_mode = mode.lower()
        else:
            raise ValueError("Output mode 必須為 'console'、'file' 或 'both'")

    def set_log_file(self, filepath: str):
        """ Set Output Place To Local File """
        self._log_file = filepath

    def enable(self):
        """ Allow Logger To Take Action """
        self._enabled = True

    def disable(self):
        """ Disallow Logger To Take Action """
        self._enabled = False

    def set_window(self, text_widget: Text):
        """ Set Output Place To Existed Text Widget In Tkinter Window """
        self._tk_window = text_widget

        # 設定 tag 顏色
        for level, color in self._tk_colors.items():
            text_widget.tag_config(level, foreground=color)

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
        if not self._enabled:
            return

        level = level.upper()
        if level not in self._level_order:
            raise ValueError(f"未知的等級：{level}")

        if self._level_order[level] < self._level_order[self._min_level]:
            return

        if _CURRENT_RUN_MODE == "RUN" and level != "ERROR":
            return

        if level == "INFO" and _CURRENT_RUN_MODE not in ["DEBUG", "DISPLAY"]:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        padded_level = level.ljust(self._max_level_len)

        if level == "HIGHLIGHT":
            formatted = f"\n[{timestamp}] [{padded_level}]: 🚀🚀🚀 {message} 🚀🚀🚀"
        elif shine:
            formatted = f"[{timestamp}] [{padded_level}]: ✨ {message} ✨"
        else:
            formatted = f"[{timestamp}] [{padded_level}]: {message}"

        # Console 輸出
        if self._output_mode in ("console", "both"):
            color = self._level_colors.get(level, "")
            if shine:
                color = color + Style.BRIGHT
            print(f"{color}{formatted}{Style.RESET_ALL}")

        # File 輸出
        if self._output_mode in ("file", "both"):
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")

        # Tkinter 輸出
        if self._tk_window:
            self._tk_window.insert("end", formatted + "\n", level)
            self._tk_window.see("end")

    # ------------------- 快捷方法 --------------------

    def debug(self, msg: str): self.log(msg, "DEBUG")
    def info(self, msg: str): self.log(msg, "INFO")
    def checkpoint(self, msg: str): self.log(msg, "CHECKPOINT")
    def success(self, msg: str): self.log(msg, "SUCCESS")
    def warning(self, msg: str): self.log(msg, "WARNING")
    def error(self, msg: str): self.log(msg, "ERROR")
    def critical(self, msg: str): self.log(msg, "CRITICAL")
    def highlight(self, msg: str): self.log(msg, "HIGHLIGHT")


def test_logger_basic_flow():
    """
    基礎測試：SingletonSystemLogger

    測試流程：
    1. 預設輸出到檔案（file），min_level=INFO，確認 DEBUG 不輸出
    2. 調整為 console + file，min_level=DEBUG，全部訊息均應輸出
    3. 調整 min_level 為 WARNING，低於此級別的訊息不輸出
    """
    logger = SingletonSystemLogger()

    logger.set_output_mode("file")
    logger.set_log_file("test_logger.log")
    logger.set_min_level("WARNING")

    print("=== [階段 1] 預設輸出到檔案，最低級別 WARNING ===")
    logger.info("INFO 訊息，預期不輸出")
    logger.debug("DEBUG 訊息，預期不輸出")
    logger.checkpoint("CHECKPOINT 訊息，預期不輸出")
    logger.success("SUCCESS 訊息，預期不輸出")
    logger.warning("WARNING 訊息，預期輸出")
    logger.error("ERROR 訊息，預期輸出")
    logger.critical("CRITICAL 訊息，預期輸出")
    print("請檢查 test_logger.log，確認 INFO 以上等級訊息。")

    print("\n=== [階段 2] 調整為 console + file，最低級別 DEBUG，全部訊息顯示 ===")
    logger.set_output_mode("both")
    logger.set_min_level("DEBUG")

    logger.info("INFO 訊息，預期輸出")
    logger.debug("DEBUG 訊息，預期輸出")
    logger.checkpoint("CHECKPOINT 訊息，預期輸出")
    logger.success("SUCCESS 訊息，預期輸出")
    logger.warning("WARNING 訊息，預期輸出")
    logger.error("ERROR 訊息，預期輸出")
    logger.critical("CRITICAL 訊息，預期輸出")

    print("\n=== [階段 3] 設定最低級別 INFO，低於此級別不輸出 ===")
    logger.set_min_level("INFO")

    logger.info("INFO 訊息，預期輸出")
    logger.debug("DEBUG 訊息，預期輸出")
    logger.checkpoint("CHECKPOINT 訊息，預期輸出")
    logger.success("SUCCESS 訊息，預期輸出")
    logger.warning("WARNING 訊息，預期輸出")
    logger.error("ERROR 訊息，預期輸出")
    logger.critical("CRITICAL 訊息，預期輸出")
    logger.highlight("HIGHLIGHT 訊息，預期輸出")

    print("\n✅ 測試完成，請確認 console 與 test_logger.log 中輸出結果。")


def test_logger_level_order_and_aliases():
    """
    等級排序與別名測試：
    - 確認 warning 與 warn 同義
    - 確認 checkpoint 層級存在並正確排序在 INFO 和 SUCCESS 之間
    - 全等級輸出以驗證排序與顏色
    """
    logger = SingletonSystemLogger()
    logger.set_output_mode("console")
    logger.set_min_level("DEBUG")

    print("=== 測試 warning 與 warn 同義 ===")
    logger.warning("warn 訊息")
    logger.warning("warning 訊息")

    print("\n=== 測試 checkpoint 層級及排序 ===")
    logger.info("Info 訊息")
    logger.debug("Debug 訊息")
    logger.checkpoint("Checkpoint 訊息")
    logger.success("Success 訊息")
    logger.warning("Warning 訊息")
    logger.error("Error 訊息")
    logger.critical("Critical 訊息")

    print("\n✅ 等級別名與排序測試完成")


def test_logger_file_output_content():
    """
    測試檔案輸出內容格式與寫入：
    - 輸出多種等級訊息至指定檔案
    - 請手動確認檔案內容格式正確
    """
    log_file = "test_file_output.log"
    logger = SingletonSystemLogger()
    logger.set_log_file(log_file)
    logger.set_output_mode("file")
    logger.set_min_level("DEBUG")

    messages = [
        ("info", "Info 訊息"),
        ("debug", "Debug 訊息"),
        ("checkpoint", "Checkpoint 訊息"),
        ("success", "Success 訊息"),
        ("warning", "Warning 訊息"),
        ("error", "Error 訊息"),
        ("critical", "Critical 訊息"),
    ]

    for level, msg in messages:
        getattr(logger, level)(msg)

    print(f"✅ 訊息已輸出至檔案 {log_file}，請手動檢查內容格式。")


def tkinter_gui_text_testing():
    # 你的 Tkinter GUI 測試視窗保持不變即可

    import tkinter as tk
    from tkinter import ttk

    class LoggerGUI(tk.Tk):
        LEVELS = ["ALL", "DEBUG", "INFO", "CHECKPOINT", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

        def __init__(self):
            super().__init__()
            self.title("Logger GUI 測試")
            self.geometry("800x400")

            self.logger = SingletonSystemLogger()
            self.text_widget = tk.Text(self, wrap="word", height=20, width=100, state=tk.NORMAL)
            self.text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            # 設定文字顏色tag（記得也加上 checkpoint）
            self.text_widget.tag_config("DEBUG", foreground="#0000ff")  # BLUE
            self.text_widget.tag_config("INFO", foreground="#000000")  # BLACK
            self.text_widget.tag_config("CHECKPOINT", foreground="#66ffff")  # LIGHTCYAN_EX
            self.text_widget.tag_config("SUCCESS", foreground="#90ee90")  # LIGHTGREEN_EX
            self.text_widget.tag_config("WARNING", foreground="#ffff00")  # YELLOW
            self.text_widget.tag_config("ERROR", foreground="#ff0000")  # RED
            self.text_widget.tag_config("CRITICAL", foreground="#ff00ff", underline=1, font=("TkDefaultFont", 10, "bold"))  # MAGENTA
            self.text_widget.tag_config("HIGHLIGHT", foreground="#ffff33", font=("TkDefaultFont", 10, "bold"))  # LIGHTYELLOW_EX

            self.logger.set_window(self.text_widget)

            self.messages = [
                ("INFO", "這是 INFO 訊息"),
                ("DEBUG", "這是 DEBUG 訊息"),
                ("CHECKPOINT", "這是 CHECKPOINT 訊息"),
                ("SUCCESS", "這是 SUCCESS 訊息"),
                ("WARNING", "這是 WARNING 訊息"),
                ("ERROR", "這是 ERROR 訊息"),
                ("CRITICAL", "這是 CRITICAL 訊息"),
                ("HIGHLIGHT", "這是 HIGHLIGHT 訊息"),
            ]

            control_frame = ttk.Frame(self)
            control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

            ttk.Label(control_frame, text="設定顯示最低等級：").pack(side=tk.LEFT)
            self.min_level_var = tk.StringVar(value="ALL")
            level_combo = ttk.Combobox(control_frame, textvariable=self.min_level_var, values=self.LEVELS, state="readonly", width=12)
            level_combo.pack(side=tk.LEFT, padx=5)
            level_combo.bind("<<ComboboxSelected>>", self.on_level_change)

            self.update_text("ALL")

        def on_level_change(self, event=None):
            selected = self.min_level_var.get()
            self.update_text(selected)

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
