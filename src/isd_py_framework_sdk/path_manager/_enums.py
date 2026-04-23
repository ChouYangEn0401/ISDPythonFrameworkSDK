from enum import Enum, auto


class PathMode(Enum):
    """
    Declares the anchor (context) used to resolve or express a path.

    Used in two complementary roles:

    1. **As ``anchor`` when registering** — tells the manager what
       ``stored_path`` is relative to.
    2. **As ``mode`` when calling ``get()``** — tells the manager in which
       representation to return the result.

    Groups
    ------

    Passthrough
    ~~~~~~~~~~~
    ABSOLUTE
        Fully-resolved OS absolute path.  No ancestry required.
        完全解析的 OS 絕對路徑，不需要任何參照點。

    Project scope  (require ``set_proj_root()`` to have been called)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    PROJ_RELATIVE
        Relative ``Path`` from the project root.
        相對於專案根目錄的相對路徑。
    PROJ_ABSOLUTE
        Absolute path composed as ``proj_root / stored_path``.
        以 ``proj_root / stored_path`` 組成的絕對路徑。

    Executable / deployment scope
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    EXE_RELATIVE
        Relative to the directory that contains the executable
        (or the entry-point script in dev mode).
        相對於執行檔所在目錄（開發模式下為入口腳本目錄）。
    EXE_ABSOLUTE
        Absolute path under the executable's directory.
        以執行檔目錄為基底的絕對路徑。
    EXE_INNER
        Inside a PyInstaller-bundled executable (``sys._MEIPASS``).
        Raises ``RuntimeError`` when not running under PyInstaller.
        PyInstaller 打包內部（``sys._MEIPASS``）；非打包環境拋出 ``RuntimeError``。

    System / OS scope
    ~~~~~~~~~~~~~~~~~
    SYSTEM_TEMP
        System temporary directory (``tempfile.gettempdir()``).
        系統暫存目錄（``tempfile.gettempdir()``）。

    User scope  (cross-platform, resolved via ``platformdirs`` when available,
                 otherwise falls back to ``pathlib.Path.home()``-based heuristics)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    USER_HOME
        User home directory (``Path.home()``).
        使用者家目錄（``Path.home()``）。
    USER_CONFIG
        User-specific configuration directory.
        Platform:  Linux ``~/.config/<app>``  |  macOS ``~/Library/Preferences``
                   Windows ``%APPDATA%``
        使用者設定目錄，依平台不同自動解析。
    USER_DATA
        User-specific application data directory.
        Platform:  Linux ``~/.local/share/<app>``  |  macOS ``~/Library/Application Support``
                   Windows ``%APPDATA%``
        使用者應用程式資料目錄。
    USER_CACHE
        User-specific cache directory.
        Platform:  Linux ``~/.cache/<app>``  |  macOS ``~/Library/Caches``
                   Windows ``%LOCALAPPDATA%\\Cache``
        使用者快取目錄。

    Runtime / process scope
    ~~~~~~~~~~~~~~~~~~~~~~~
    CWD
        Current working directory at the moment of the call (``Path.cwd()``).
        呼叫時的當前工作目錄。
    SCRIPT_DIR
        Directory of the top-level entry-point script (``sys.argv[0]``).
        Useful for CLI tools that ship data files next to the script.
        入口腳本（``sys.argv[0]``）所在目錄，適合 CLI 工具與腳本型部署。

    Development tooling
    ~~~~~~~~~~~~~~~~~~~~
    VIRTUAL_ENV
        Active virtual environment root (reads ``VIRTUAL_ENV`` env-var).
        Raises ``RuntimeError`` when no venv is active.
        當前啟用的虛擬環境根目錄（讀取 ``VIRTUAL_ENV`` 環境變數）。
    PACKAGE_RESOURCE
        Package-internal resource directory resolved via
        ``importlib.resources`` / ``importlib.metadata``.
        Suitable for read-only data bundled *inside* a Python package
        (works for both editable installs and wheel installs).
        透過 ``importlib.resources`` 解析的套件內部資源目錄。
        適用於隨套件發布的唯讀資料（editable 安裝與 wheel 安裝均適用）。
    """

    # --- Passthrough ---
    ABSOLUTE        = auto()

    # --- Project scope ---
    PROJ_RELATIVE   = auto()
    PROJ_ABSOLUTE   = auto()

    # --- Executable / deployment scope ---
    EXE_RELATIVE    = auto()
    EXE_ABSOLUTE    = auto()
    EXE_INNER       = auto()

    # --- System / OS scope ---
    SYSTEM_TEMP     = auto()

    # --- User scope ---
    USER_HOME       = auto()
    USER_CONFIG     = auto()
    USER_DATA       = auto()
    USER_CACHE      = auto()

    # --- Runtime / process scope ---
    CWD             = auto()
    SCRIPT_DIR      = auto()

    # --- Development tooling ---
    VIRTUAL_ENV     = auto()
    PACKAGE_RESOURCE = auto()
