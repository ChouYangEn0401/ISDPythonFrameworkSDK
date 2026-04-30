import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from isd_py_framework_sdk.message_logger import (
    DarkThemeTerminalAdapter,
    DarkThemeTkLabelAdapter,
    DarkThemeTkinterAdapter,
    DarkThemeTtkLabelAdapter,
    FileAdapter,
    LightThemeTerminalAdapter,
    LightThemeTkLabelAdapter,
    LightThemeTkinterAdapter,
    LightThemeTtkLabelAdapter,
    SingletonSystemLogger,
)


class ConfigDebuggerPanel:
    """
    改良版 ConfigDebuggerPanel：
    - 保留原有功能。
    - 加入 Console Message Text 區域。
    - 移除固定 10 秒關閉，改為外部事件觸發關閉。
    """

    def __init__(self, master, initial_config_path=None):
        self.master = master
        master.title("參數模式切換應用程式")
        master.geometry("900x700")
        self.logger = SingletonSystemLogger()
        self.current_theme = "dark"
        self.file_log_path = Path(__file__).with_name("_legacy_.log")
        self.file_adapter = FileAdapter("INFO", self.file_log_path, mode="w")

        self.config_data = None

        # 狀態顏色設定
        self.STATE_MANUAL_INIT = ("手動模式啟用", "blue")
        self.STATE_AUTO = ("自動參數模式啟用", "green")
        self.STATE_MANUAL_LOADED = ("手動參數模式啟用", "orange")

        # UI 設定
        self._setup_ui()
        self._set_theme(self.current_theme)

        # 初始化載入（若有初始路徑）
        if initial_config_path:
            self._initial_load(initial_config_path)
        else:
            self._update_ui(*self.STATE_MANUAL_INIT, content="請點選下方按鈕載入設定檔...")
            self.logger.info("請點選下方按鈕載入設定檔...")

    def _setup_logger(self):
        """集中設定 logger adapters，避免在事件中重複建立。"""
        self.logger.clear_adapters()

        if self.current_theme == "dark":
            self.console_adapter = DarkThemeTkinterAdapter("DEBUG", tk_window=self.console_text)
            self.terminal_adapter = DarkThemeTerminalAdapter("INFO")
            self.tk_label_adapter = DarkThemeTkLabelAdapter("INFO", tk_label=self.latest_tk_label)
            self.ttk_label_adapter = DarkThemeTtkLabelAdapter("INFO", ttk_label=self.latest_ttk_label)
        else:
            self.console_adapter = LightThemeTkinterAdapter("DEBUG", tk_window=self.console_text)
            self.terminal_adapter = LightThemeTerminalAdapter("INFO")
            self.tk_label_adapter = LightThemeTkLabelAdapter("INFO", tk_label=self.latest_tk_label)
            self.ttk_label_adapter = LightThemeTtkLabelAdapter("INFO", ttk_label=self.latest_ttk_label)

        # GUI 文字區（主輸出）
        self.logger.register_adapter(self.console_adapter)

        # 終端機輸出（可選）
        self.logger.register_adapter(self.terminal_adapter)

        # Label 顯示最後一條訊息（示範 tk.Label / ttk.Label adapter）
        self.logger.register_adapter(self.tk_label_adapter)
        self.logger.register_adapter(self.ttk_label_adapter)

        # 檔案輸出（可選，便於追蹤）
        self.logger.register_adapter(self.file_adapter)

    def _set_theme(self, theme: str):
        self.current_theme = theme
        if theme == "dark":
            self.console_text.configure(bg="#1e1e1e", fg="#00ff7f")
            self.latest_tk_label.configure(bg="#2a2a2a", fg="#ffffff")
            self.theme_btn.configure(text="切換到淺色主題")
        else:
            self.console_text.configure(bg="#ffffff", fg="#1f6f3d")
            self.latest_tk_label.configure(bg="#ffffff", fg="#000000")
            self.theme_btn.configure(text="切換到深色主題")

        self._setup_logger()
        self.logger.checkpoint(f"已切換至 {theme} 主題")

    def toggle_theme(self):
        next_theme = "light" if self.current_theme == "dark" else "dark"
        self._set_theme(next_theme)

    def _setup_ui(self):
        """建立主 UI 結構"""
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10)

        main_frame = tk.Frame(self.master, padx=20, pady=20, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True)

        # 狀態 Label
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Microsoft YaHei', 28, 'bold'),
            fg='white',
            relief=tk.RAISED,
            pady=15,
            padx=10,
            wraplength=800
        )
        self.status_label.pack(pady=(0, 15), fill='x')

        # 載入按鈕
        self.load_button = ttk.Button(
            main_frame,
            text="點擊載入 Config (JSON)",
            command=self.manual_load_config
        )
        self.load_button.pack(pady=10, ipadx=20)

        self.theme_btn = ttk.Button(
            main_frame,
            text="切換到淺色主題",
            command=self.toggle_theme,
        )
        self.theme_btn.pack(pady=(0, 10), ipadx=20)

        label_latest = tk.Label(main_frame, text="Latest Message（tk.Label）:", font=('Microsoft YaHei', 11, 'bold'), bg='#f0f0f0')
        label_latest.pack(pady=(0, 3), anchor='w')

        self.latest_tk_label = tk.Label(
            main_frame,
            text="尚未有訊息",
            font=('Consolas', 10),
            anchor='w',
            padx=8,
            pady=6,
            bg='#2a2a2a',
            fg='#ffffff',
        )
        self.latest_tk_label.pack(fill='x')

        label_latest_ttk = tk.Label(main_frame, text="Latest Message（ttk.Label）:", font=('Microsoft YaHei', 11, 'bold'), bg='#f0f0f0')
        label_latest_ttk.pack(pady=(8, 3), anchor='w')

        self.latest_ttk_label = ttk.Label(main_frame, text="尚未有訊息", anchor='w')
        self.latest_ttk_label.pack(fill='x')

        # === Config Text 區塊 ===
        label_config = tk.Label(main_frame, text="設定檔內容預覽:", font=('Microsoft YaHei', 13, 'bold'), bg='#f0f0f0')
        label_config.pack(pady=(10, 5), anchor='w')

        config_frame = tk.Frame(main_frame)
        config_frame.pack(fill='both', expand=True)

        config_scrollbar = tk.Scrollbar(config_frame)
        config_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.config_text = tk.Text(
            config_frame,
            wrap=tk.WORD,
            yscrollcommand=config_scrollbar.set,
            font=('Consolas', 10),  # 字體縮小
            bg='#2d2d2d',
            fg='#e0e0e0',
            insertbackground='white',
            bd=0,
            relief=tk.SUNKEN,
            padx=8,
            pady=8,
            height=10
        )
        self.config_text.pack(side=tk.LEFT, fill='both', expand=True)
        config_scrollbar.config(command=self.config_text.yview)

        # === Console Message 區塊 ===
        label_console = tk.Label(main_frame, text="Console Messages:", font=('Microsoft YaHei', 13, 'bold'), bg='#f0f0f0')
        label_console.pack(pady=(15, 5), anchor='w')

        console_frame = tk.Frame(main_frame)
        console_frame.pack(fill='both', expand=True)

        console_scrollbar = tk.Scrollbar(console_frame)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.console_text = tk.Text(
            console_frame,
            wrap=tk.WORD,
            yscrollcommand=console_scrollbar.set,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#00ff7f',
            insertbackground='white',
            bd=0,
            relief=tk.SUNKEN,
            padx=8,
            pady=8,
            height=10
        )
        self.console_text.pack(side=tk.LEFT, fill='both', expand=True)
        console_scrollbar.config(command=self.console_text.yview)

    def _update_ui(self, status_text, color, content):
        """更新標題與 config 區域內容"""
        self.status_label.config(text=status_text, background=color)
        self.config_text.delete('1.0', tk.END)
        self.config_text.insert(tk.END, content)

    def _load_json_file(self, file_path):
        """讀取 JSON 檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            content_str = json.dumps(self.config_data, indent=4, ensure_ascii=False)
            return True, content_str
        except FileNotFoundError:
            return False, f"錯誤: 找不到檔案路徑 '{file_path}'"
        except json.JSONDecodeError as e:
            return False, f"錯誤: JSON 解碼失敗.\n錯誤訊息: {e}"
        except Exception as e:
            return False, f"發生意外錯誤: {e}"

    def _initial_load(self, path):
        """啟動時自動載入"""
        success, content = self._load_json_file(path)
        if success:
            self._update_ui(*self.STATE_AUTO, content=content)
            self.logger.success(f"[AUTO] 成功載入設定檔：{path}")
        else:
            self._update_ui(*self.STATE_MANUAL_INIT, content=f"自動載入失敗。\n{content}")
            self.logger.error(f"[AUTO] 自動載入失敗：{content}")

    def manual_load_config(self):
        """手動載入"""
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="選擇設定檔 (config.json)"
        )

        if not file_path:
            return

        success, content = self._load_json_file(file_path)
        if success:
            self._update_ui(*self.STATE_MANUAL_LOADED, content=content)
            self.logger.success(f"[MANUAL] 成功載入設定檔：{file_path}")
        else:
            self._update_ui(self.STATE_MANUAL_LOADED[0], self.STATE_MANUAL_LOADED[1], content=content)
            self.logger.error(f"[MANUAL] 手動載入失敗：{content}")

    # === 由外部 EventManager 觸發 ===
    def close_after_delay(self, delay_ms=10000):
        """外部呼叫以在任務完成後延遲關閉 GUI"""
        self.logger.info(f"任務完成，{delay_ms//1000} 秒後自動關閉...")
        self.master.after(delay_ms, self.on_close)

    def on_close(self):
        """確保檔案 adapter 關閉，避免資源未釋放。"""
        try:
            self.logger.flush_all()
            self.file_adapter.close()
        finally:
            self.master.destroy()


def simulate_logging(panel: ConfigDebuggerPanel):
    """模擬外部事件觸發 log 輸出"""
    logger = panel.logger
    logger.debug("debug: demo started")
    logger.info("開始初始化系統...")
    logger.checkpoint("checkpoint: 準備載入資料")
    logger.success("已載入設定檔")
    logger.warning("這是警告訊息")
    logger.error("測試錯誤輸出")
    logger.critical("這是 critical 測試訊息")
    logger.highlight("高亮提示：這是 highlight 訊息")

    # 使用 adapter 能力覆寫最後一行（進度更新場景）
    panel.console_adapter.overwrite_last_line("INFO", "[模擬進度] 95%")

    logger.shiny_log("完成", "SUCCESS")
    logger.flush_all()

if __name__ == "__main__":
    root = tk.Tk()
    panel = ConfigDebuggerPanel(root)
    root.protocol("WM_DELETE_WINDOW", panel.on_close)

    # 模擬啟動後延遲 2 秒再開始 logger 測試
    root.after(2000, lambda: simulate_logging(panel))

    # 模擬任務結束後關閉視窗
    root.after(8000, lambda: panel.close_after_delay(3000))

    root.mainloop()