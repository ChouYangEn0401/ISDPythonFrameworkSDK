from abc import ABC, abstractmethod
from pathlib import Path
from colorama import Fore, Style

from personal_experiment.enum import LevelOrder, LogLevelLiteral


class LoggerAdapterBase(ABC):
    def __init__(self, LEVEL_FILTER: LogLevelLiteral, *args, **kwargs):
        self.level_filter = LEVEL_FILTER
    
    # ------------------- Core Method --------------------

    @abstractmethod
    def broadcast(self, level: str, formatted: str, shine: bool = False): pass

    def set_filtered_level(
            self,
            level: LogLevelLiteral
    ):
        """ Set The Lowest Showcase Level """
        if self._have_level(level, b_stop_when_error=True):
            self._filtered_level = level
    
    # ------------------- Status Checker --------------------

    @staticmethod
    def help():
        """ Show The Level For Each Usable Mode """
        print("此訊息順序預期為： DEBUG < INFO < CHECKPOINT < SUCCESS < WARNING < ERROR < CRITICAL")
        for key, item in LevelOrder.items():
            print(key, f"at level {item}.")

    @staticmethod
    def level_formator(level: str) -> str:
        return level.upper()  ## can add more cleaning method in future !!

    @staticmethod
    def _have_level(level: str, b_stop_when_error: bool = False) -> bool:
        if level not in LevelOrder:
            if b_stop_when_error:
                raise ValueError(f"未知的等級：{level}")
            else:
                return False
        return True
    
    def _pass_filter(self, level: LogLevelLiteral) -> bool:
        return LevelOrder[level] > LevelOrder[self._filtered_level]


class TerminalAdapter(LoggerAdapterBase, ABC):
    # Console 輸出
    def broadcast(self, level: str, formatted: str, shine: bool = False):
        level = self.level_formator(level)
        if self._pass_filter(level):
            return
        
        if self._output_mode in ("console", "both"):
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
    # File 輸出
    def __init__(self, LEVEL_FILTER: LogLevelLiteral, outputfile: Path = Path("app_output.log"), *args, **kwargs):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._log_file = outputfile

    def broadcast(self, level: str, formatted: str, shine: bool = False):
        level = self.level_formator(level)
        if self._pass_filter(level):
            return
        
        if self._output_mode in ("file", "both"):
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")

class TkinterAdapter(LoggerAdapterBase):
    # Tkinter 輸出
    def __init__(self, LEVEL_FILTER: LogLevelLiteral, tk_window=None, *args, **kwargs):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._tk_window = tk_window

    def broadcast(self, level: str, formatted: str, shine: bool = False):
        level = self.level_formator(level)
        if self._pass_filter(level):
            return
        
        if self._tk_window:
            self._tk_window.insert("end", formatted + "\n", level)
            self._tk_window.see("end")




