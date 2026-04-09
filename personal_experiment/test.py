from personal_experiment.logger import SingletonSystemLogger


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
    test_logger_file_output_content()
    tkinter_gui_text_testing()
