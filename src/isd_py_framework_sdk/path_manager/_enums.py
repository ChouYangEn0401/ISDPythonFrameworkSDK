from enum import Enum, auto


class PathMode(Enum):
    """
    Members
    -------
    ABSOLUTE
        Fully-resolved OS absolute path.  No ancestry required.
        完全解析的作業系統絕對路徑。無需參照祖先目錄。
    CWD
        Current working directory at the moment of the call.
        呼叫時的當前工作目錄。

    PROJ_RELATIVE
        Relative to the project root configured via ``set_proj_root()``.
        Requires ``set_proj_root()`` to have been called.
        相對於透過 `set_proj_root()` 設定的專案根目錄。需先呼叫 `set_proj_root()`。
    PROJ_ABSOLUTE
        Absolute path constructed from ``proj_root / stored_path``.
        Semantically equivalent to ``PROJ_RELATIVE`` but always returns
        an absolute ``Path`` object.
        由 `proj_root / stored_path` 建構的絕對路徑。在語意上等同於 `PROJ_RELATIVE`，但總是返回絕對的 `Path` 物件。

    EXE_RELATIVE
        Relative to the directory containing the executable (or the
        entry-point script in dev mode).
        相對於可執行檔所在目錄（開發模式下為入口腳本所在目錄）。
    EXE_ABSOLUTE
        Absolute path constructed from ``exe_side_root / stored_path``.
        由 `exe_side_root / stored_path` 構成的絕對路徑。

    EXE_INNER
        Inside a PyInstaller-bundled executable (``sys._MEIPASS``).
        Raises ``RuntimeError`` when not running under PyInstaller.
        位於 PyInstaller 打包的可執行檔內部（`sys._MEIPASS`）。若非在 PyInstaller 下執行則會拋出 `RuntimeError`。
    SYSTEM_TEMP
        System temporary directory (``tempfile.gettempdir()``).
        系統暫存目錄（`tempfile.gettempdir()`）。
    """

    ABSOLUTE      = auto()
    CWD           = auto()

    PROJ_RELATIVE = auto()
    PROJ_ABSOLUTE = auto()

    EXE_RELATIVE  = auto()
    EXE_ABSOLUTE  = auto()
    
    EXE_INNER     = auto()
    SYSTEM_TEMP   = auto()
