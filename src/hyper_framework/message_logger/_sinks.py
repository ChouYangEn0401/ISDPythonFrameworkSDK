import os
from typing import Dict, TYPE_CHECKING

from colorama import Fore, Style

if TYPE_CHECKING:
    from tkinter import Text

_LogLevelOrder = Dict[str, int]


class LogSink:
    """
    所有輸出目標（sink）的基底類別。

    每個 sink 負責：
      - 持有自己的最低顯示等級（min_level）
      - 決定是否允許某等級通過（allow）
      - 執行實際的輸出動作（emit）
    """

    def __init__(self, min_level: str = "DEBUG"):
        self._min_level = min_level.upper()

    def set_min_level(self, level: str) -> None:
        """設定此 sink 的最低顯示等級。"""
        self._min_level = level.upper()

    def allow(self, level: str, level_order: _LogLevelOrder) -> bool:
        """判斷此等級是否達到此 sink 的顯示門檻。"""
        return level_order.get(level, 0) >= level_order.get(self._min_level, 0)

    def emit(self, formatted: str, level: str, shine: bool = False) -> None:
        """輸出已格式化的訊息。子類必須實作。"""
        raise NotImplementedError


class TerminalSink(LogSink):
    """
    輸出到 terminal（console），支援 ANSI 顏色。

    預設顏色主題由環境變數 CONSOLE_BG 控制（dark / light，預設 dark）。
    也可在建構時傳入 theme 參數覆蓋。
    """

    _DEFAULT_DARK: Dict[str, str] = {
        "DEBUG":      Fore.BLUE,
        "INFO":       Fore.WHITE,
        "CHECKPOINT": Fore.LIGHTCYAN_EX,
        "SUCCESS":    Fore.LIGHTGREEN_EX,
        "WARNING":    Fore.YELLOW,
        "ERROR":      Fore.RED,
        "CRITICAL":   Fore.MAGENTA,
        "HIGHLIGHT":  Fore.LIGHTYELLOW_EX + Style.BRIGHT,
    }

    _DEFAULT_LIGHT: Dict[str, str] = {
        "DEBUG":      Fore.BLUE,
        "INFO":       Fore.BLACK,
        "CHECKPOINT": Fore.CYAN,
        "SUCCESS":    Fore.GREEN,
        "WARNING":    Fore.MAGENTA,
        "ERROR":      Fore.RED,
        "CRITICAL":   Fore.MAGENTA,
        "HIGHLIGHT":  Fore.BLUE + Style.BRIGHT,
    }

    def __init__(self, min_level: str = "DEBUG", theme: str = None):
        """
        Parameters
        ----------
        min_level : str
            最低顯示等級，預設 DEBUG。
        theme : str, optional
            "dark" 或 "light"。若未傳入則讀取環境變數 CONSOLE_BG，預設 dark。
        """
        super().__init__(min_level)
        _theme = (theme or os.environ.get("CONSOLE_BG", "dark")).lower()
        self._colors = self._DEFAULT_LIGHT if _theme == "light" else self._DEFAULT_DARK

    def emit(self, formatted: str, level: str, shine: bool = False) -> None:
        color = self._colors.get(level, "")
        if shine:
            color = color + Style.BRIGHT
        print(f"{color}{formatted}{Style.RESET_ALL}")


class FileSink(LogSink):
    """
    輸出到本機檔案（append 模式，UTF-8）。
    """

    def __init__(self, filepath: str = "app.log", min_level: str = "DEBUG"):
        """
        Parameters
        ----------
        filepath : str
            輸出檔案路徑，預設 "app.log"。
        min_level : str
            最低顯示等級，預設 DEBUG。
        """
        super().__init__(min_level)
        self._filepath = filepath

    def set_filepath(self, filepath: str) -> None:
        """變更輸出檔案路徑。"""
        self._filepath = filepath

    def emit(self, formatted: str, level: str, shine: bool = False) -> None:
        with open(self._filepath, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")


class TkinterSink(LogSink):
    """
    輸出到 Tkinter Text widget，依等級自動套用顏色 tag。

    注意：Tkinter 只允許從主執行緒操作 widget。
    若有跨執行緒 logging 需求，請在呼叫端使用 widget.after() 搭配 queue 處理。
    """

    DEFAULT_COLORS: Dict[str, str] = {
        "DEBUG":      "#0000ff",  # 藍
        "INFO":       "#000000",  # 黑
        "CHECKPOINT": "#66ffff",  # 淺青
        "SUCCESS":    "#228B22",  # 深綠
        "WARNING":    "#C19A6B",  # 焦糖
        "ERROR":      "#ff0000",  # 紅
        "CRITICAL":   "#ff00ff",  # 洋紅
        "HIGHLIGHT":  "#ffff33",  # 亮黃
    }

    def __init__(
        self,
        widget: "Text",
        min_level: str = "DEBUG",
        colors: Dict[str, str] = None,
    ):
        """
        Parameters
        ----------
        widget : tkinter.Text
            要輸出至的 Text widget，建構時自動設定顏色 tag。
        min_level : str
            最低顯示等級，預設 DEBUG。
        colors : dict, optional
            自訂等級→顏色對應表（hex string）。若未傳入則使用 DEFAULT_COLORS。
        """
        super().__init__(min_level)
        self._widget = widget
        _colors = colors or self.DEFAULT_COLORS
        for level_name, color in _colors.items():
            widget.tag_config(level_name, foreground=color)

    def emit(self, formatted: str, level: str, shine: bool = False) -> None:
        self._widget.insert("end", formatted + "\n", level)
        self._widget.see("end")
