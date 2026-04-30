import tkinter as tk
from tkinter import ttk
from typing import Optional
from .base import ColorLoggerBase, ColorProvider


class TkinterColorProvider(ColorProvider):
    COLOR_MAP = {
        # 'red': "red", 'green': "green", 'yellow': "yellow", 'blue': "blue",
        # 'magenta': "magenta", 'cyan': "cyan", 'white': "white", 'black': "black",
        # 'gray': "gray", 'reset': "black",  # fallback
    }
    def get_color_code(self, color: Optional[ColorProvider.ColorLiteral]) -> str:
        return self.COLOR_MAP.get(color, self.COLOR_MAP['reset'])

# ──────────────────────────────
# 顏色主題提供器：亮色主題版
# ──────────────────────────────
class LightThemeColorProvider(TkinterColorProvider):
    """
    適用於亮色主題 (白底 / 淺灰底) 的顏色配置。
    用於 tk.Text、Label 等 GUI 控件。
    """
    COLOR_MAP = {
        # === 高對比主要色系 ===
        'red': "#d32f2f",          # 錯誤、警告
        'green': "#2e7d32",        # 成功訊息
        'yellow': "#f9a825",       # 警示、注意
        'blue': "#1565c0",         # 一般資訊
        'magenta': "#9c27b0",      # 特殊事件
        'cyan': "#0097a7",         # 系統訊息
        'white': "#000000",        # 白底時反轉，黑字
        'gray': "#555555",         # 一般文字
        'black': "#000000",        # 主體文字
        # === 擴充配色 ===
        'orange': "#ef6c00",       # 警告
        'purple': "#7e57c2",       # 特殊提示
        'pink': "#d81b60",         # 附加資訊
        'lime': "#9e9d24",         # 次級成功
        'aqua': "#00838f",         # 系統提示
        'teal': "#00695c",         # 狀態提示
        'amber': "#ffb300",        # 警示訊息
        'light_gray': "#999999",   # 淡灰
        'reset': "#333333",        # 預設回退色
    }
# ──────────────────────────────
# 顏色主題提供器：暗色主題版
# ──────────────────────────────
class DarkThemeColorProvider(TkinterColorProvider):
    """
    適用於深色主題 (如黑底、灰底) 的顏色配置。
    可用於 Console、Tkinter Text / Label 等元件。
    """
    COLOR_MAP = {
        # === 亮色系 (主要訊息) ===
        'red': "#ff4c4c",         # 錯誤、警告
        'green': "#32cd32",       # 成功訊息
        'yellow': "#ffeb3b",      # 警示訊息
        'blue': "#4ca3dd",        # 一般資訊
        'magenta': "#ff66ff",     # 特殊事件
        'cyan': "#00e5ff",        # 系統訊息
        'white': "#f5f5f5",       # 高亮白
        'gray': "#9e9e9e",        # 一般文字
        'black': "#000000",       # 背景基底
        # === 補充色系 ===
        'orange': "#ffa500",
        'purple': "#b266ff",
        'pink': "#ff99cc",
        'lime': "#b4ff66",
        'aqua': "#66ffff",
        'teal': "#20b2aa",
        'amber': "#ffc107",
        'light_gray': "#cccccc",
        'reset': "#d0d0d0",       # 預設回退
    }


# ──────────────────────────────
# tk.Label
# ──────────────────────────────
class TkLabelLogger(ColorLoggerBase[TkinterColorProvider]):
    def __init__(self, label: tk.Label, provider: Optional[TkinterColorProvider] = None):
        super().__init__(provider or TkinterColorProvider())
        self.label = label

    def write(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None, newline=True):
        fg = self.color_provider.get_color_code(color)
        text = msg + ("\n" if newline else "")
        self.label.config(text=text, fg=fg)

    def overwrite(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None):
        self.write(msg, color=color, newline=False)

    def flush(self):
        self.label.update_idletasks()


# ──────────────────────────────
# ttk.Label
# ──────────────────────────────
class TtkLabelLogger(ColorLoggerBase[TkinterColorProvider]):
    def __init__(self, label: ttk.Label, provider: Optional[TkinterColorProvider] = None):
        super().__init__(provider or TkinterColorProvider())
        self.label = label

    def write(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None, newline=True):
        fg = self.color_provider.get_color_code(color)
        text = msg + ("\n" if newline else "")
        style_name = f"ColorLogger.{fg}.TLabel"
        style = ttk.Style()
        style.configure(style_name, foreground=fg)
        self.label.configure(text=text, style=style_name)

    def overwrite(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None):
        self.write(msg, color=color, newline=False)

    def flush(self):
        self.label.update_idletasks()


# ──────────────────────────────
# tk.Text Logger
# ──────────────────────────────
class TkTextLogger(ColorLoggerBase[TkinterColorProvider]):
    """
    支援彩色輸出到 tk.Text 的 Logger。
    - 根據 tag 顏色輸出文字。
    - 自動滾動到最底部。
    """
    def __init__(self, text: tk.Text, provider: Optional[TkinterColorProvider] = None):
        super().__init__(provider or TkinterColorProvider())
        self.text = text

    def write(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None, newline=True):
        fg = self.color_provider.get_color_code(color)
        tag = color or fg or 'reset'
        if not tag.isidentifier():
            tag = 'reset'

        # 若該顏色 tag 尚未存在，建立它
        if tag not in self.text.tag_names():
            self.text.tag_configure(tag, foreground=fg)

        text = msg + ("\n" if newline else "")
        self.text.insert("end", text, tag)
        self.text.see("end")
        self.text.update_idletasks()

    def overwrite(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None):
        """覆寫最後一行內容"""

        # 如果 Text 為空，直接寫入
        if self.text.index("end-1c") == "1.0":
            self.write(msg, color=color, newline=True)
            return

        try:
            # 找到最後一行的行首和行尾
            last_line_start = self.text.index("end-2c linestart")  # end-1c 是最後一個字元，end-2c 是最後一行最後一個字元
            last_line_end = self.text.index("end-1c")  # 文字結尾的索引
            self.text.delete(last_line_start, last_line_end)
        except tk.TclError:
            # 保險措施
            self.text.delete("1.0", "end")

        self.write(msg, color=color, newline=True)

    def flush(self):
        self.text.update_idletasks()

