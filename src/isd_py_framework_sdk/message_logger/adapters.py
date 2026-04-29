from abc import ABC, abstractmethod
from pathlib import Path
from colorama import Fore, Style

from isd_py_framework_sdk.message_logger.base import LoggerAdapterBase
from isd_py_framework_sdk.message_logger.base.levels import LogLevelLiteral


class TerminalAdapter(LoggerAdapterBase, ABC):
    """彩色 terminal 輸出的抽象基底；子類提供 _level_colors。"""

    def broadcast(self, level: str, formatted: str, shine: bool = False):
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        color = self._level_colors.get(level, "")
        if shine:
            color = color + Style.BRIGHT
        print(f"{color}{formatted}{Style.RESET_ALL}")
        
class DarkThemeTerminalAdapter(TerminalAdapter):
    _level_colors = {
        "DEBUG":      Fore.BLUE,                               # 藍色，適合詳細除錯
        "INFO":       Fore.WHITE,                              # 白色，穩重訊息
        "CHECKPOINT": Fore.LIGHTCYAN_EX,                       # 淺青色，醒目且專業，和INFO不同
        "SUCCESS":    Fore.LIGHTGREEN_EX,                      # 淺綠色，成功訊息
        "WARNING":    Fore.YELLOW,                             # 黃色，警告訊息
        "ERROR":      Fore.RED,                                # 紅色，錯誤訊息
        "CRITICAL":   Fore.MAGENTA,                            # 洋紅色，致命錯誤
        "HIGHLIGHT":  Fore.LIGHTYELLOW_EX + Style.BRIGHT,      # 搭配明亮黃色 + 強化字體
    }
    
class LightThemeTerminalAdapter(TerminalAdapter):
    _level_colors = {
        "DEBUG":      Fore.BLUE,                               # 藍色，適合詳細除錯
        "INFO":       Fore.BLACK,                              # 黑色，穩重訊息
        "CHECKPOINT": Fore.CYAN,                               # 深青色，醒目且專業，和INFO不同
        "SUCCESS":    Fore.GREEN,                              # 綠色，成功訊息
        "WARNING":    Fore.MAGENTA,                            # 洋紅色，強調警告訊息
        "ERROR":      Fore.RED,                                # 紅色，錯誤訊息
        "CRITICAL":   Fore.MAGENTA,                            # 洋紅色，致命錯誤
        "HIGHLIGHT":  Fore.LIGHTYELLOW_EX + Style.BRIGHT,      # 搭配明亮黃色 + 強化字體
    }


class FileAdapter(LoggerAdapterBase):
    """本機檔案輸出（UTF-8 append 模式）。"""

    def __init__(self, LEVEL_FILTER: LogLevelLiteral, outputfile: Path = Path("app_output.log"), *args, **kwargs):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._log_file = outputfile

    def broadcast(self, level: str, formatted: str, shine: bool = False):
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")


class TkinterAdapter(LoggerAdapterBase, ABC):
    """Tkinter Text widget 彩色輸出的抽象基底；子類提供 _level_colors（hex 字串）。"""

    from tkinter import Tk

    def __init__(self, LEVEL_FILTER: LogLevelLiteral, tk_window: Tk, *args, **kwargs):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._tk_window = tk_window
        if self._tk_window:
            self._configure_tags()

    def reset_tk_window(self, tk_window: Tk):
        """替換或設定 Tkinter Text widget，並重新套用顏色標籤。"""
        self._tk_window = tk_window
        if self._tk_window:
            self._configure_tags()

    def _configure_tags(self):
        """為每個等級設定 Tkinter Text tag 顏色（含 _SHINE 粗體變體）。"""
        for level, color in self._level_colors.items():
            self._tk_window.tag_configure(level, foreground=color)
            self._tk_window.tag_configure(f"{level}_SHINE", foreground=color, font=("TkDefaultFont", 10, "bold"))

    def broadcast(self, level: str, formatted: str, shine: bool = False):
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        if self._tk_window:
            tag = f"{level}_SHINE" if shine else level
            self._tk_window.insert("end", formatted + "\n", tag)
            self._tk_window.see("end")

class DarkThemeTkinterAdapter(TkinterAdapter):
    _level_colors = {
        "DEBUG":      "#5599ff",  # 藍色
        "INFO":       "#ffffff",  # 白色
        "CHECKPOINT": "#66ffff",  # 淺青
        "SUCCESS":    "#66ff66",  # 淺綠
        "WARNING":    "#ffcc00",  # 黃色
        "ERROR":      "#ff4444",  # 紅色
        "CRITICAL":   "#ff44ff",  # 洋紅
        "HIGHLIGHT":  "#ffff33",  # 亮黃
    }

class LightThemeTkinterAdapter(TkinterAdapter):
    _level_colors = {
        "DEBUG":      "#0000cc",  # 深藍
        "INFO":       "#000000",  # 黑色
        "CHECKPOINT": "#007777",  # 深青
        "SUCCESS":    "#228B22",  # 森林綠
        "WARNING":    "#aa007f",  # 洋紅（淺色背景可見）
        "ERROR":      "#cc0000",  # 深紅
        "CRITICAL":   "#880088",  # 深洋紅
        "HIGHLIGHT":  "#0055ff",  # 亮藍
    }

