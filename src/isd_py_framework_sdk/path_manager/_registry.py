"""
Internal path registry — PathEntry + PathRegistry.

These are implementation details; external code should interact with
the manager via ``IPathManager`` / ``SingletonPathManager``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from ._enums import PathMode


@dataclass
class PathEntry:
    """
    A single registered path record.

    Attributes
    ----------
    tag : str
        Unique identifier used to look up this path.
    stored_path : Path
        The path as provided by the caller.  May be relative or absolute
        depending on *anchor*.
    anchor : PathMode
        Declares what *stored_path* is relative to:

        - ``ABSOLUTE``      → already fully resolved; used as-is
        - ``PROJ_RELATIVE`` → relative to the project root
        - ``PROJ_ABSOLUTE`` → same interpretation as PROJ_RELATIVE; alias kept for symmetry
        - ``EXE_RELATIVE``  → relative to the exe/script directory
        - ``EXE_ABSOLUTE``  → same interpretation as EXE_RELATIVE
        - ``EXE_INNER``     → relative to ``sys._MEIPASS``
        - ``SYSTEM_TEMP``   → relative to the system temp directory
        - ``CWD``           → relative to the CWD at registration time

    description : str
        Human-readable note about this path's purpose (used in
        ``list_tags()`` and ``info()`` output).
    """

    tag: str
    stored_path: Path
    anchor: PathMode
    description: str = ""

    def __post_init__(self) -> None:
        self.stored_path = Path(self.stored_path)


class PathRegistry:
    """
    In-memory dictionary of ``PathEntry`` objects keyed by tag.

    All mutating methods are straightforward dict operations.  Thread
    safety for concurrent **reads** is provided implicitly by CPython's
    GIL; the ``SingletonPathManager`` is the authoritative lock point
    for concurrent **writes** if needed in future.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, PathEntry] = {}

    # ------------------------------------------------------------------ #
    #  Mutation                                                            #
    # ------------------------------------------------------------------ #

    def add(self, entry: PathEntry, b_force_add: bool = False) -> None:
        """Insert or overwrite the entry for ``entry.tag``."""
        if entry.tag in self._entries and not b_force_add:
            raise KeyError(f"Path tag '{entry.tag}' is already registered.")
        self._entries[entry.tag] = entry

    def remove(self, tag: str) -> None:
        """
        Remove the entry for *tag*.

        Raises
        ------
        KeyError
            If *tag* is not currently registered.
        """
        if tag not in self._entries:
            raise KeyError(f"Path tag '{tag}' is not registered.")
        del self._entries[tag]

    # ------------------------------------------------------------------ #
    #  Retrieval                                                           #
    # ------------------------------------------------------------------ #

    def get(self, tag: str) -> PathEntry:
        """
        Return the entry for *tag*.

        Raises
        ------
        KeyError
            If *tag* is not currently registered.
        """
        if tag not in self._entries:
            raise KeyError(
                f"Path tag '{tag}' is not registered.  "
                f"Available tags: {sorted(self._entries)}"
            )
        return self._entries[tag]

    def has(self, tag: str) -> bool:
        """Return ``True`` if *tag* is currently registered."""
        return tag in self._entries

    def all_entries(self) -> Dict[str, PathEntry]:
        """Return a shallow copy of all entries (tag → PathEntry)."""
        return dict(self._entries)
