import sys
from typing import Optional
from .base import LoggerBase, ColorProvider, ColorLoggerBase


class ConsoleColorProvider(ColorProvider):
    COLOR_MAP = {
        'red':     "\033[91m",
        'green':   "\033[92m",
        'yellow':  "\033[93m",
        'blue':    "\033[94m",
        'magenta': "\033[95m",
        'cyan':    "\033[96m",
        'white':   "\033[97m",
        'black':   "\033[90m",
        'gray':    "\033[90m",
        'reset':   "\033[0m",
    }

    def get_color_code(self, color: Optional[ColorProvider.ColorLiteral]) -> str:
        return self.COLOR_MAP.get(color, self.COLOR_MAP['reset'])


class ConsoleLogger(ColorLoggerBase[ConsoleColorProvider]):
    def __init__(self, provider: Optional[ConsoleColorProvider] = None):
        super().__init__(provider or ConsoleColorProvider())

    def write(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None, newline: bool = True):
        code = self.color_provider.get_color_code(color)
        reset = self.color_provider.get_color_code('reset')

        if newline:
            print(f"{code}{msg}{reset}")
        else:
            sys.stdout.write(f"{code}{msg}{reset}")
            sys.stdout.flush()

    def overwrite(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None):
        """使用 \r 覆寫當前行並清除殘留"""
        code = self.color_provider.get_color_code(color)
        reset = self.color_provider.get_color_code('reset')
        sys.stdout.write("\r" + " " * 120 + "\r")  # 清除前一行
        sys.stdout.write(f"{code}{msg}{reset}")
        sys.stdout.flush()

    def flush(self):
        sys.stdout.flush()
