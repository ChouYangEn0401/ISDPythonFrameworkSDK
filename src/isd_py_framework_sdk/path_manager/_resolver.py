"""
EnvironmentResolver — runtime environment detection and anchor directories.

All public methods return fully-resolved absolute ``Path`` objects.
Internal logic is kept stateless (pure static methods) so it can be
called freely without instantiation.
"""

import os
import sys
import tempfile
from pathlib import Path


class EnvironmentResolver:
    """
    Detects the runtime environment and provides the anchor directory
    for each ``PathMode``.

    PyInstaller detection
    ---------------------
    PyInstaller sets ``sys.frozen = True`` and ``sys._MEIPASS`` (the
    temp directory where bundled files are unpacked).  Both attributes
    must be present for a positive detection.

    Exe-side root in dev mode
    -------------------------
    When not running under PyInstaller, ``exe_side_root()`` uses
    ``sys.argv[0]`` (the entry-point script) as the heuristic.  This
    mirrors the path where the exe would sit in a real deployment.

    User directories
    ----------------
    Resolved via ``platformdirs`` when installed, otherwise via
    ``Path.home()``-based heuristics that work on Windows / macOS / Linux.
    The *app_name* parameter (default ``"app"``) is used by ``platformdirs``
    to scope the directory (e.g. ``~/.config/<app_name>``).
    """

    # ------------------------------------------------------------------ #
    #  Environment detection                                               #
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_pyinstaller() -> bool:
        """Return ``True`` when running inside a PyInstaller-frozen executable."""
        return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

    # ------------------------------------------------------------------ #
    #  Anchor directories                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def exe_inner_root() -> Path:
        """
        Root of bundled data inside a PyInstaller executable (``sys._MEIPASS``).

        Raises
        ------
        RuntimeError
            When not running under PyInstaller.
        """
        if not EnvironmentResolver.is_pyinstaller():
            raise RuntimeError(
                "PathMode.EXE_INNER is only available when the application "
                "is running as a PyInstaller-frozen executable.  "
                "(sys._MEIPASS is not set in this process.)"
            )
        return Path(sys._MEIPASS).resolve()  # type: ignore[attr-defined]

    @staticmethod
    def exe_side_root() -> Path:
        """
        Directory that *contains* the executable (or the entry-point script
        in dev mode).

        - **PyInstaller**: ``Path(sys.executable).parent``
        - **Dev / plain Python**: ``Path(sys.argv[0]).parent``
        """
        if EnvironmentResolver.is_pyinstaller():
            return Path(sys.executable).resolve().parent
        return Path(sys.argv[0]).resolve().parent

    @staticmethod
    def system_temp_root() -> Path:
        """System temporary directory (platform-specific, e.g. ``/tmp`` or ``%TEMP%``)."""
        return Path(tempfile.gettempdir()).resolve()

    @staticmethod
    def cwd() -> Path:
        """Current working directory at the moment of the call."""
        return Path.cwd().resolve()

    @staticmethod
    def script_dir() -> Path:
        """
        Directory of the top-level entry-point script (``sys.argv[0]``).

        In PyInstaller mode this is the same as ``exe_side_root()``.
        """
        return Path(sys.argv[0]).resolve().parent

    @staticmethod
    def user_home() -> Path:
        """User home directory (``Path.home()``)."""
        return Path.home().resolve()

    @staticmethod
    def user_config(app_name: str = "app") -> Path:
        """
        User configuration directory for *app_name*.

        Tries ``platformdirs.user_config_dir`` first; falls back to:
        - Linux/macOS: ``~/.config/<app_name>``
        - Windows:     ``%APPDATA%/<app_name>``
        """
        try:
            import platformdirs
            return Path(platformdirs.user_config_dir(app_name)).resolve()
        except ImportError:
            pass
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path.home() / ".config"
        return (base / app_name).resolve()

    @staticmethod
    def user_data(app_name: str = "app") -> Path:
        """
        User application data directory for *app_name*.

        Tries ``platformdirs.user_data_dir`` first; falls back to:
        - Linux:   ``~/.local/share/<app_name>``
        - macOS:   ``~/Library/Application Support/<app_name>``
        - Windows: ``%APPDATA%/<app_name>``
        """
        try:
            import platformdirs
            return Path(platformdirs.user_data_dir(app_name)).resolve()
        except ImportError:
            pass
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home() / ".local" / "share"
        return (base / app_name).resolve()

    @staticmethod
    def user_cache(app_name: str = "app") -> Path:
        """
        User cache directory for *app_name*.

        Tries ``platformdirs.user_cache_dir`` first; falls back to:
        - Linux:   ``~/.cache/<app_name>``
        - macOS:   ``~/Library/Caches/<app_name>``
        - Windows: ``%LOCALAPPDATA%/<app_name>/Cache``
        """
        try:
            import platformdirs
            return Path(platformdirs.user_cache_dir(app_name)).resolve()
        except ImportError:
            pass
        if sys.platform == "win32":
            local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            return (local / app_name / "Cache").resolve()
        elif sys.platform == "darwin":
            return (Path.home() / "Library" / "Caches" / app_name).resolve()
        else:
            return (Path.home() / ".cache" / app_name).resolve()

    @staticmethod
    def virtual_env() -> Path:
        """
        Root of the currently active virtual environment.

        Reads the ``VIRTUAL_ENV`` environment variable set by
        ``venv`` / ``virtualenv`` / ``conda activate``.

        Raises
        ------
        RuntimeError
            When no virtual environment is active.
        """
        venv = os.environ.get("VIRTUAL_ENV")
        if not venv:
            raise RuntimeError(
                "PathMode.VIRTUAL_ENV is only available when a virtual "
                "environment is active (VIRTUAL_ENV env-var is not set)."
            )
        return Path(venv).resolve()

        """System temporary directory (platform-specific, e.g. ``/tmp`` or ``%TEMP%``)."""
        return Path(tempfile.gettempdir()).resolve()

    @staticmethod
    def cwd() -> Path:
        """Current working directory at the moment of the call."""
        return Path.cwd().resolve()

