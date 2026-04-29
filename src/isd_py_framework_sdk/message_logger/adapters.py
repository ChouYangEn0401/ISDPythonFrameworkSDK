"""
adapters.py — 所有內建 Adapter 實作

內建 Adapter 一覽：
    TerminalAdapter（抽象）
        ├── DarkThemeTerminalAdapter   彩色 console（深色終端）
        └── LightThemeTerminalAdapter  彩色 console（淺色終端）

    FileAdapter                        thread-safe 本機日誌檔案

    TkinterAdapter（抽象）
        ├── DarkThemeTkinterAdapter    Tkinter Text widget（深色主題）
        └── LightThemeTkinterAdapter   Tkinter Text widget（淺色主題）

自訂 Adapter：
    繼承 LoggerAdapterBase 並實作 broadcast() 即可。
    參見 LoggerAdapterBase 說明。
"""
from __future__ import annotations

import threading
from abc import ABC
from pathlib import Path

from colorama import Fore, Style

from .base.LoggerAdapterBase import LoggerAdapterBase
from .base.levels import LogLevelLiteral


# ─────────────────────────────────────────────────────────────────────────────
# Terminal Adapters
# ─────────────────────────────────────────────────────────────────────────────

class TerminalAdapter(LoggerAdapterBase, ABC):
    """
    彩色 terminal 輸出的抽象基底。
    子類透過類別屬性 ``_level_colors`` 提供每個 level 的 colorama 色碼。
    ``shine=True`` 時額外疊加 Style.BRIGHT。
    """

    _level_colors: dict[str, str] = {}

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        color = self._level_colors.get(level, "")
        if shine:
            color = color + Style.BRIGHT
        print(f"{color}{formatted}{Style.RESET_ALL}")


class DarkThemeTerminalAdapter(TerminalAdapter):
    """適合深色 / 黑色終端背景的彩色 console adapter。"""
    _level_colors = {
        "DEBUG":      Fore.BLUE,
        "INFO":       Fore.WHITE,
        "CHECKPOINT": Fore.LIGHTCYAN_EX,
        "SUCCESS":    Fore.LIGHTGREEN_EX,
        "WARNING":    Fore.YELLOW,
        "ERROR":      Fore.RED,
        "CRITICAL":   Fore.MAGENTA,
        "HIGHLIGHT":  Fore.LIGHTYELLOW_EX + Style.BRIGHT,
    }


class LightThemeTerminalAdapter(TerminalAdapter):
    """適合淺色 / 白色終端背景的彩色 console adapter。"""
    _level_colors = {
        "DEBUG":      Fore.BLUE,
        "INFO":       Fore.BLACK,
        "CHECKPOINT": Fore.CYAN,
        "SUCCESS":    Fore.GREEN,
        "WARNING":    Fore.MAGENTA,
        "ERROR":      Fore.RED,
        "CRITICAL":   Fore.MAGENTA,
        "HIGHLIGHT":  Fore.LIGHTYELLOW_EX + Style.BRIGHT,
    }


# ─────────────────────────────────────────────────────────────────────────────
# File Adapter
# ─────────────────────────────────────────────────────────────────────────────

class FileAdapter(LoggerAdapterBase):
    """
    Thread-safe 本機檔案輸出（UTF-8，預設 append 模式）。

    Args:
        LEVEL_FILTER: 最低顯示等級。
        output_file:  輸出路徑，預設為 ``app_output.log``。
        mode:         ``"a"``（追加，預設）或 ``"w"``（覆寫）。
        auto_flush:   每次寫入後立即 flush，預設 True。
    """

    def __init__(
        self,
        LEVEL_FILTER: LogLevelLiteral,
        output_file: Path = Path("app_output.log"),
        *,
        mode: str = "a",
        auto_flush: bool = True,
        **kwargs,
    ):
        super().__init__(LEVEL_FILTER, **kwargs)
        self._log_file = Path(output_file)
        self._mode = mode
        self._auto_flush = auto_flush
        self._lock = threading.Lock()
        self._file = self._log_file.open(mode, encoding="utf-8")

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        with self._lock:
            self._file.write(formatted + "\n")
            if self._auto_flush:
                self._file.flush()

    def flush(self) -> None:
        """強制 flush 至磁碟。"""
        with self._lock:
            self._file.flush()

    def close(self) -> None:
        """關閉檔案句柄。建議在程式結束前呼叫。"""
        with self._lock:
            try:
                self._file.close()
            except Exception:
                pass

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Tkinter Adapters
# ─────────────────────────────────────────────────────────────────────────────

class TkinterAdapter(LoggerAdapterBase, ABC):
    """
    Tkinter ``tk.Text`` widget 彩色輸出的抽象基底。

    子類透過類別屬性 ``_level_colors`` 提供每個 level 的 hex 色碼。
    ``shine=True`` 時額外套用粗體（``<LEVEL>_SHINE`` tag）。

    支援延遲注入 widget：
        先以 ``tk_window=None`` 建立 adapter，等 UI 初始化完成後
        再呼叫 ``set_tk_window(widget)`` 綁定。

    注意：Tkinter 只允許從主執行緒操作 widget。
    若有跨執行緒 logging 需求，請在呼叫端使用 ``widget.after()`` 搭配 ``queue.Queue``。
    """

    _level_colors: dict[str, str] = {}

    def __init__(
        self,
        LEVEL_FILTER: LogLevelLiteral,
        tk_window=None,
        *args,
        **kwargs,
    ):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._tk_window = tk_window
        if self._tk_window is not None:
            self._configure_tags()

    # --- Widget 管理 ----------------------------------------------------------

    def set_tk_window(self, tk_window) -> None:
        """
        綁定（或替換）Tkinter Text widget，並套用所有等級的顏色 tag。

        可在 UI 初始化完成後再呼叫（延遲注入）。
        """
        self._tk_window = tk_window
        if self._tk_window is not None:
            self._configure_tags()

    # 向下相容的別名
    reset_tk_window = set_tk_window

    def _configure_tags(self) -> None:
        """為每個等級建立 Tkinter Text tag 與 _SHINE 粗體變體。"""
        for level, color in self._level_colors.items():
            self._tk_window.tag_configure(level, foreground=color)
            self._tk_window.tag_configure(
                f"{level}_SHINE",
                foreground=color,
                font=("TkDefaultFont", 10, "bold"),
            )

    # --- Broadcast ------------------------------------------------------------

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        if self._tk_window is None:
            return
        tag = f"{level}_SHINE" if shine else level
        self._tk_window.insert("end", formatted + "\n", tag)
        self._tk_window.see("end")

    def flush(self) -> None:
        """呼叫 widget 的 update_idletasks() 確保 UI 即時重繪。"""
        if self._tk_window is not None:
            self._tk_window.update_idletasks()

    def overwrite_last_line(self, level: str, formatted: str, shine: bool = False) -> None:
        """
        覆寫 widget 最後一行的內容（用於進度更新等場景）。

        若 widget 為空則退化為普通 ``broadcast()``。
        """
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        if self._tk_window is None:
            return

        # 若 widget 為空，直接寫入
        if self._tk_window.index("end-1c") == "1.0":
            self.broadcast(level, formatted, shine)
            return

        try:
            last_line_start = self._tk_window.index("end-2c linestart")
            last_line_end   = self._tk_window.index("end-1c")
            self._tk_window.delete(last_line_start, last_line_end)
        except Exception:
            self._tk_window.delete("1.0", "end")

        self.broadcast(level, formatted, shine)


class DarkThemeTkinterAdapter(TkinterAdapter):
    """適合深色背景（如 #1e1e1e）的 Tkinter Text widget adapter。"""
    _level_colors = {
        "DEBUG":      "#5599ff",
        "INFO":       "#ffffff",
        "CHECKPOINT": "#66ffff",
        "SUCCESS":    "#66ff66",
        "WARNING":    "#ffcc00",
        "ERROR":      "#ff4444",
        "CRITICAL":   "#ff44ff",
        "HIGHLIGHT":  "#ffff33",
    }


class LightThemeTkinterAdapter(TkinterAdapter):
    """適合淺色背景（如 #ffffff）的 Tkinter Text widget adapter。"""
    _level_colors = {
        "DEBUG":      "#0000cc",
        "INFO":       "#000000",
        "CHECKPOINT": "#007777",
        "SUCCESS":    "#228B22",
        "WARNING":    "#aa007f",
        "ERROR":      "#cc0000",
        "CRITICAL":   "#880088",
        "HIGHLIGHT":  "#0055ff",
    }


# ─────────────────────────────────────────────────────────────────────────────
# tk.Label Adapters
# ─────────────────────────────────────────────────────────────────────────────

class TkLabelAdapter(LoggerAdapterBase, ABC):
    """
    Level-aware ``tk.Label`` adapter 的抽象基底。

    Label 每次只顯示最新一筆訊息，以前景色區分等級。
    子類透過類別屬性 ``_level_colors`` 提供每個 level 的 hex 色碼。
    ``shine=True`` 時字體加粗。

    支援延遲注入 widget：
        先以 ``tk_label=None`` 建立 adapter，等 UI 初始化完成後
        再呼叫 ``set_tk_label(label)`` 綁定。
    """

    _level_colors: dict[str, str] = {}

    def __init__(
        self,
        LEVEL_FILTER: LogLevelLiteral,
        tk_label=None,
        *args,
        **kwargs,
    ):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._tk_label = tk_label

    def set_tk_label(self, tk_label) -> None:
        """綁定（或替換）tk.Label widget（支援延遲注入）。"""
        self._tk_label = tk_label

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        if self._tk_label is None:
            return
        color = self._level_colors.get(level, "")
        if shine:
            self._tk_label.config(text=formatted, fg=color, font=("TkDefaultFont", 10, "bold"))
        else:
            self._tk_label.config(text=formatted, fg=color)

    def flush(self) -> None:
        """呼叫 label 的 update_idletasks() 確保 UI 即時重繪。"""
        if self._tk_label is not None:
            self._tk_label.update_idletasks()


class DarkThemeTkLabelAdapter(TkLabelAdapter):
    """適合深色背景的 tk.Label adapter。"""
    _level_colors = {
        "DEBUG":      "#5599ff",
        "INFO":       "#ffffff",
        "CHECKPOINT": "#66ffff",
        "SUCCESS":    "#66ff66",
        "WARNING":    "#ffcc00",
        "ERROR":      "#ff4444",
        "CRITICAL":   "#ff44ff",
        "HIGHLIGHT":  "#ffff33",
    }


class LightThemeTkLabelAdapter(TkLabelAdapter):
    """適合淺色背景的 tk.Label adapter。"""
    _level_colors = {
        "DEBUG":      "#0000cc",
        "INFO":       "#000000",
        "CHECKPOINT": "#007777",
        "SUCCESS":    "#228B22",
        "WARNING":    "#aa007f",
        "ERROR":      "#cc0000",
        "CRITICAL":   "#880088",
        "HIGHLIGHT":  "#0055ff",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ttk.Label Adapters
# ─────────────────────────────────────────────────────────────────────────────

class TtkLabelAdapter(LoggerAdapterBase, ABC):
    """
    Level-aware ``ttk.Label`` adapter 的抽象基底。

    與 ``TkLabelAdapter`` 相同語意，但透過 ``ttk.Style`` 設定前景色，
    以相容 ttk 的主題系統。
    子類透過類別屬性 ``_level_colors`` 提供每個 level 的 hex 色碼。
    ``shine=True`` 時字體加粗。

    支援延遲注入 widget：
        先以 ``ttk_label=None`` 建立 adapter，等 UI 初始化完成後
        再呼叫 ``set_ttk_label(label)`` 綁定。
    """

    _level_colors: dict[str, str] = {}

    def __init__(
        self,
        LEVEL_FILTER: LogLevelLiteral,
        ttk_label=None,
        *args,
        **kwargs,
    ):
        super().__init__(LEVEL_FILTER, *args, **kwargs)
        self._ttk_label = ttk_label

    def set_ttk_label(self, ttk_label) -> None:
        """綁定（或替換）ttk.Label widget（支援延遲注入）。"""
        self._ttk_label = ttk_label

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        import tkinter.ttk as _ttk
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        if self._ttk_label is None:
            return
        color = self._level_colors.get(level, "")
        font_spec = ("TkDefaultFont", 10, "bold") if shine else ("TkDefaultFont", 10)
        style_name = f"Logger{level}{'Shine' if shine else ''}.TLabel"
        style = _ttk.Style()
        style.configure(style_name, foreground=color, font=font_spec)
        self._ttk_label.configure(text=formatted, style=style_name)

    def flush(self) -> None:
        """呼叫 label 的 update_idletasks() 確保 UI 即時重繪。"""
        if self._ttk_label is not None:
            self._ttk_label.update_idletasks()


class DarkThemeTtkLabelAdapter(TtkLabelAdapter):
    """適合深色背景的 ttk.Label adapter。"""
    _level_colors = {
        "DEBUG":      "#5599ff",
        "INFO":       "#ffffff",
        "CHECKPOINT": "#66ffff",
        "SUCCESS":    "#66ff66",
        "WARNING":    "#ffcc00",
        "ERROR":      "#ff4444",
        "CRITICAL":   "#ff44ff",
        "HIGHLIGHT":  "#ffff33",
    }


class LightThemeTtkLabelAdapter(TtkLabelAdapter):
    """適合淺色背景的 ttk.Label adapter。"""
    _level_colors = {
        "DEBUG":      "#0000cc",
        "INFO":       "#000000",
        "CHECKPOINT": "#007777",
        "SUCCESS":    "#228B22",
        "WARNING":    "#aa007f",
        "ERROR":      "#cc0000",
        "CRITICAL":   "#880088",
        "HIGHLIGHT":  "#0055ff",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Network / Remote Stub Adapters
# ─────────────────────────────────────────────────────────────────────────────

from ..helpers.decorators.lifecycle import test_func  # noqa: E402


class HTMLAdapter(LoggerAdapterBase):
    """
    HTML 輸出 adapter stub — 尚未實作。
    繼承並覆寫 ``broadcast()`` 以實作自訂 HTML 輸出邏輯。
    """

    @test_func("HTMLAdapter.broadcast() is a no-op stub. Subclass and implement to use.")
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        pass


class HTTPAdapter(LoggerAdapterBase):
    """
    HTTP 遠端 log 輸出 adapter stub — 尚未實作。
    繼承並覆寫 ``broadcast()`` 以實作 HTTP 送出邏輯（例如 requests.post）。
    """

    @test_func("HTTPAdapter.broadcast() is a no-op stub. Subclass and implement to use.")
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        pass


class DBAdapter(LoggerAdapterBase):
    """
    資料庫 log 輸出 adapter stub — 尚未實作。
    繼承並覆寫 ``broadcast()`` 以實作資料庫寫入邏輯。
    """

    @test_func("DBAdapter.broadcast() is a no-op stub. Subclass and implement to use.")
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        pass


class WebsocketAdapter(LoggerAdapterBase):
    """
    WebSocket log 輸出 adapter stub — 尚未實作。
    繼承並覆寫 ``broadcast()`` 以實作 WebSocket 推送邏輯。
    """

    @test_func("WebsocketAdapter.broadcast() is a no-op stub. Subclass and implement to use.")
    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        pass
