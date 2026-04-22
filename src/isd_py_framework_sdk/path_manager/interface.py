"""
IPathManager — abstract interface for path managers.

Implement this interface to create project-specific path managers that
can participate in larger multi-project or multi-process topologies.
The reference implementation is ``SingletonPathManager``.

Design contract
---------------
* ``set_proj_root`` — configure the project-root anchor
* ``register`` / ``unregister`` / ``has`` — manage the tag → path registry
* ``get`` — resolve a tag to a concrete ``Path``; accepts either a
  ``PathMode`` (single representation) or a ``Waterfall`` (fallback chain)
* ``exists`` — non-raising existence check
* ``list_tags`` — introspect the registry (debugging / documentation)
* ``resolve_conflict`` — compute a safe write path respecting a
  ``ConflictStrategy`` (§7 reserved; skeleton)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

from ._enums import PathMode
from ._waterfall import Waterfall
from ._conflict import ConflictStrategy


class IPathManager(ABC):
    """Abstract base class for all path managers in the ISD framework."""

    # ------------------------------------------------------------------ #
    #  Configuration                                                       #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def set_proj_root(
        self,
        path: Union[Path, str],
        *,
        levels_up: int = 0,
    ) -> None:
        """
        Set the project-root directory used for ``PROJ_*`` modes.

        Parameters
        ----------
        path :
            A directory path **or** a ``__file__`` value from any module.
            If *path* points to a file, its parent directory is the
            starting point.
        levels_up :
            How many parent levels to ascend after resolving *path*.

            Example — this file lives at ``project/src/pkg/config.py``
            and we want ``project/`` as the root::

                pm.set_proj_root(__file__, levels_up=2)
        """
        ...

    # ------------------------------------------------------------------ #
    #  Registry                                                            #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def register(
        self,
        tag: str,
        path: Union[Path, str],
        anchor: PathMode,
        *,
        description: str = "",
    ) -> None:
        """
        Register *path* under *tag* with an explicit *anchor*.

        *anchor* is **required** — it declares which base directory *path*
        is relative to.  Re-registering an existing tag silently overwrites.
        """
        ...

    @abstractmethod
    def unregister(self, tag: str) -> None:
        """Remove *tag* from the registry.  Raises ``KeyError`` if absent."""
        ...

    @abstractmethod
    def has(self, tag: str) -> bool:
        """Return ``True`` if *tag* is currently registered."""
        ...

    # ------------------------------------------------------------------ #
    #  Resolution                                                          #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def get(
        self,
        tag: str,
        waterfall: Optional[Waterfall] = None,
        *,
    ) -> Path:
        """
        """
        ...

    @abstractmethod
    def exists(
        self,
        tag: str,

    @abstractmethod
    def exists(self, tag: str) -> bool:
        """
        Non-raising existence check.

        Returns ``True`` if the resolved path exists on disk;
        ``False`` for any error (tag not found, anchor not set, etc.).
        """
        ...

    # ------------------------------------------------------------------ #
    #  Introspection                                                       #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def list_tags(self) -> Dict[str, str]:
        """Return ``{tag: description}`` for all registered entries."""
        ...

    @abstractmethod
    def info(self) -> str:
        """Return a diagnostic string: environment state + full tag registry."""
        ...

    # ------------------------------------------------------------------ #
    #  Conflict resolution                                                 #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def resolve_conflict(
        self,
        tag: str,
        *,
        strategy: Optional[ConflictStrategy] = None,
        mode: PathMode = PathMode.ABSOLUTE,
    ) -> Path:
        """
        Compute a safe write path for *tag*, applying *strategy* if the
        resolved path already exists on disk.

        If *strategy* is ``None``, the manager uses its configured default
        (``IncrementSuffixStrategy`` out of the box).

        This method does **not** perform any I/O — computing the path only.
        Writing is the caller's responsibility.

        Returns
        -------
        Path
            The path the caller should write to (may differ from the
            resolved path when a conflict was detected).
        """
        ...

