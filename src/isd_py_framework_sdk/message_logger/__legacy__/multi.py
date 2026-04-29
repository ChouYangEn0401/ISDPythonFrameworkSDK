from .base import LoggerBase

class MultiLogger(LoggerBase):
    def __init__(self, *loggers: LoggerBase):
        self.loggers = loggers

    def write(self, msg: str, *, color=None, newline=True):
        for l in self.loggers:
            l.write(msg, color=color, newline=newline)

    def overwrite(self, msg: str, *, color=None):
        for l in self.loggers:
            l.overwrite(msg, color=color)

    def flush(self):
        for l in self.loggers:
            l.flush()

