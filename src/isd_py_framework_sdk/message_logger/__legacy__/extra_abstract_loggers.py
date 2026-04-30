from .base import LoggerBase

class HTMLLogger(LoggerBase):
    def write(self, msg: str, *, color=None, newline=True):
        pass

class HTTPLogger(LoggerBase):
    def write(self, msg: str, *, color=None, newline=True):
        pass

class DBLogger(LoggerBase):
    def write(self, msg: str, *, color=None, newline=True):
        pass

class WebsocketLogger(LoggerBase):
    def write(self, msg: str, *, color=None, newline=True):
        pass
