"""
EnvironmentResolver — runtime environment detection and anchor directories.

All public methods return fully-resolved absolute ``Path`` objects.
Internal logic is kept stateless (pure static methods) so it can be
called freely without instantiation.
"""

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

        This is the natural location for data files shipped next to the exe,
        e.g. ``dist/MyApp/data/``.
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
