"""
File-conflict resolution strategies.

When a write target already exists on disk, a ``ConflictStrategy``
decides what path to write to instead.  The strategy does **not**
perform any I/O; it only computes and returns a path.  The caller is
responsible for the actual write operation.

Built-in strategies
-------------------
``OverwriteStrategy``
    Return the original path unchanged — the caller will overwrite.
``SkipIfExistsStrategy``
    Return the original path unchanged — the caller should detect
    ``resolved == original`` and skip the write.
``TimestampSuffixStrategy``
    Append ``_YYYYMMDD_HHMMSS`` before the extension.
    Example: ``result.xlsx`` → ``result_20260422_153012.xlsx``
``IncrementSuffixStrategy``
    Append ``_001``, ``_002``, … until a free filename is found.
    Example: ``result.xlsx`` → ``result_001.xlsx``

Custom strategies
-----------------
Subclass ``ConflictStrategy`` and implement ``resolve(path) -> Path``::

    from isd_py_framework_sdk.path_manager import ConflictStrategy

    class ArchiveStrategy(ConflictStrategy):
        def __init__(self, archive_dir: Path):
            self._archive_dir = archive_dir

        def resolve(self, path: Path) -> Path:
            # Move the conflicting file to archive_dir, then return original
            import shutil, datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self._archive_dir / f"{path.stem}_{ts}{path.suffix}"
            shutil.move(str(path), dest)
            return path  # original path is now free

Note
----
Full write-orchestration (``ConflictManager``) is reserved for a future
release — see ``dev_plan.md`` §7.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class ConflictStrategy(ABC):
    """
    Abstract base for file-conflict resolution strategies.

    Implement ``resolve(path) -> Path`` to provide custom behaviour.
    Override ``conflict_info()`` for custom diagnostic messages.
    """
    """
    But I Wonder If A Double Check Is Needed, Because If The Request Is Asked In Identical Same Second,
    The Suffixing Still May Return A Conflicted Path.
    """

    @abstractmethod
    def resolve(self, path: Path) -> Path:
        """
        Given a *path* that already exists on disk, return the path
        that should actually be written to.

        The returned path may be identical to *path* (overwrite / skip
        semantics) or a new sibling path (suffix strategies).

        This method must **not** perform any file I/O.
        """
        ...

    def conflict_info(self, original: Path, resolved: Path) -> str:
        """Human-readable description of the conflict-resolution decision."""
        if original == resolved:
            return f"[CONFLICT] Target already exists — overwriting: {original}"
        return (
            f"[CONFLICT] '{original}' already exists "
            f"→ redirecting write to '{resolved}'"
        )



# ------------------------------------------------------------------ #
#  Built-in strategies                                                 #
# ------------------------------------------------------------------ #

class OverwriteStrategy(ConflictStrategy):
    """Always overwrite the existing file without renaming."""

    def resolve(self, path: Path) -> Path:
        return path

    def conflict_info(self, original: Path, resolved: Path) -> str:
        return f"[CONFLICT] Overwriting existing file: {original}"

class SkipIfExistsStrategy(ConflictStrategy):
    """
    Return the original path unchanged.

    The caller should compare ``resolved == original`` to decide
    whether to skip the write operation.
    """

    def resolve(self, path: Path) -> Path:
        return path

    def conflict_info(self, original: Path, resolved: Path) -> str:
        return f"[CONFLICT] '{original}' already exists — skipping write."

class TimestampSuffixStrategy(ConflictStrategy):
    """
    Append a ``_YYYYMMDD_HHMMSS`` timestamp before the file extension.

    Example: ``result.xlsx`` → ``result_20260422_153012.xlsx``

    Note: two calls within the same second will produce the same
    candidate name.  Use ``IncrementSuffixStrategy`` if uniqueness
    within a second is required.
    """

    def resolve(self, path: Path) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return path.with_name(f"{path.stem}_{ts}{path.suffix}")

class IncrementSuffixStrategy(ConflictStrategy):
    """
    Append ``_001``, ``_002``, … until a free filename is found.

    Example: ``result.xlsx`` → ``result_001.xlsx``
    (If ``result_001.xlsx`` also exists, tries ``result_002.xlsx``, etc.)

    Parameters
    ----------
    max_attempts :
        Stop searching after this many attempts.  Raises ``RuntimeError``
        if exceeded.  Default is ``99999``.
    """

    def __init__(self, max_attempts: int = 99999) -> None:
        self._max = max_attempts

    def resolve(self, path: Path) -> Path:
        parent = path.parent
        stem = path.stem
        suffix = path.suffix
        for i in range(1, self._max + 1):
            candidate = parent / f"{stem}_{i:03d}{suffix}"
            if not candidate.exists():
                return candidate
        raise RuntimeError(
            f"IncrementSuffixStrategy: could not find a free filename for "
            f"'{path}' after {self._max} attempts."
        )
