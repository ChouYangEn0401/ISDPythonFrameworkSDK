"""Robust config-file discovery across dev / venv / PyInstaller environments.

The same code needs to find ``.env`` (or ``config.yaml`` …) whether it runs:

* from source during development (walk up from the current directory),
* inside a virtual environment, or
* as a frozen PyInstaller / cx_Freeze executable (look next to the ``.exe``).

:func:`find_config_file` returns ``None`` when nothing is found, leaving the
"is this fatal?" decision to the caller.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional

__all__ = ["find_config_file", "is_frozen"]


def is_frozen() -> bool:
    """True under PyInstaller / cx_Freeze (``sys.frozen`` is set)."""
    return bool(getattr(sys, "frozen", False))


def _executable_dir() -> Path:
    return Path(sys.executable).resolve().parent


def _iter_parents(start: Path) -> Iterable[Path]:
    current = start.resolve()
    while True:
        yield current
        if current.parent == current:
            break
        current = current.parent


def find_config_file(
    filename: str = ".env",
    *,
    explicit_path: Optional[str | Path] = None,
    search_from: Optional[str | Path] = None,
) -> Optional[Path]:
    """Locate *filename*, returning its :class:`Path` or ``None``.

    Search order:

    1. ``explicit_path`` if given (raises :class:`FileNotFoundError` if it does
       not exist — an explicit request that fails should be loud).
    2. Next to the executable, when running frozen.
    3. ``search_from`` (or the current working directory), then each parent
       directory up to the filesystem root.
    """
    if explicit_path is not None:
        p = Path(explicit_path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Specified config file not found: {p}")
        return p

    if is_frozen():
        candidate = _executable_dir() / filename
        if candidate.exists():
            return candidate

    start = Path(search_from) if search_from else Path.cwd()
    for parent in _iter_parents(start):
        candidate = parent / filename
        if candidate.exists():
            return candidate

    return None
