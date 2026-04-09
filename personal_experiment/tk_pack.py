from tkinter import Text
from colorama import Fore, Style

_tk_colors = {
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
