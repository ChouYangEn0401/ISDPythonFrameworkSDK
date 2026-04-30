from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar, Literal


class LoggerBase(ABC):
    """最小可用 logger 介面"""
    @abstractmethod
    def write(self, msg: str, *, newline: bool = True):
        pass

    def overwrite(self, msg: str):
        self.write(msg, newline=False)

    def flush(self):
        pass


C = TypeVar("C", bound="ColorProvider")

class ColorProvider(ABC):
    ColorLiteral = Literal['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'black', 'gray', 'reset']
    @abstractmethod
    def get_color_code(self, color: ColorLiteral) -> str:
        ...


class ColorLoggerBase(LoggerBase, Generic[C]):
    """支援顏色的 logger"""
    def __init__(self, color_provider: Optional[C] = None):
        self.color_provider = color_provider

    @abstractmethod
    def write(self, msg: str, *, color: Optional[ColorProvider.ColorLiteral] = None, newline: bool = True):
        pass
