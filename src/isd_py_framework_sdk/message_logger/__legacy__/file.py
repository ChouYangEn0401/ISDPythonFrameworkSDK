import threading
from .base import LoggerBase


class FileLogger(LoggerBase):
    """
    Thread-safe file logger
    """

    def __init__(
        self,
        filepath: str,
        *,
        mode: str = "a",
        encoding: str = "utf-8",
        auto_flush: bool = True,
    ):
        """
        Args
        ----
        filepath : str
            log file location
        mode : str (default="a")
            "a" → append
            "w" → overwrite
        encoding : str
        auto_flush : bool
            automatically flush after write
        """
        self.filepath = filepath
        self.mode = mode
        self.encoding = encoding
        self.auto_flush = auto_flush

        self._file = open(self.filepath, self.mode, encoding=self.encoding)
        self._lock = threading.Lock()

    def write(self, msg: str, *, color=None, newline=True):
        """
        Write string to file
        color is ignored
        """
        out = msg + ("\n" if newline else "")

        with self._lock:
            self._file.write(out)
            if self.auto_flush:
                self._file.flush()

    def overwrite(self, msg: str, *, color=None):
        """
        File can't truly do overwrite
        → fallback to write()
        """
        self.write(msg, color=color, newline=True)

    def flush(self):
        with self._lock:
            self._file.flush()

    def close(self):
        with self._lock:
            try:
                self._file.close()
            except Exception:
                pass

    def __del__(self):
        # 防止忘記 close
        try:
            self.close()
        except Exception:
            pass
