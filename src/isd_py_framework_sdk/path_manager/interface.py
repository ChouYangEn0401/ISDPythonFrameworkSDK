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
        *,
        anchor: PathMode = PathMode.PROJ_RELATIVE,
        description: str = "",
    ) -> None:
        """
        Register *path* under *tag*.

        Re-registering an existing tag silently overwrites the previous
        entry.

        Parameters
        ----------
        tag :
            Unique string identifier.
        path :
            The path to store.
            Interpretation depends on *anchor*.
        anchor :
            How to interpret *path* (see ``PathMode`` docstring).
            Defaults to ``PROJ_RELATIVE``.
        description :
            Human-readable note for documentation and ``info()`` output.
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
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> Path:
        """
        Resolve the path registered under *tag*.

        Parameters
        ----------
        tag :
            A previously registered tag.
        mode :
            ``PathMode``
                Express the path in this representation.  Does **not**
                require the path to exist on disk.

                - ``ABSOLUTE`` → fully-resolved OS path (default)
                - ``PROJ_RELATIVE`` → relative ``Path`` from ``proj_root``
                - ``EXE_ABSOLUTE`` → absolute from exe/script directory
                - etc.

            ``Waterfall``
                Try each step in order and return the first path that
                **exists on disk**.  Raises ``FileNotFoundError`` if no
                step yields an existing path (diagnostic info included).

        Returns
        -------
        Path
            Resolved path.  May be relative when *mode* is
            ``PROJ_RELATIVE`` or ``EXE_RELATIVE``.

        Raises
        ------
        KeyError
            Tag not registered.
        RuntimeError
            Required anchor (e.g. ``proj_root``) not configured.
        FileNotFoundError
            Waterfall exhausted with no existing path found.
        """
        ...

    @abstractmethod
    def exists(
        self,
        tag: str,
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> bool:
        """
        Non-raising wrapper around ``get``.

        Returns ``True`` if the resolved path exists on disk;
        ``False`` for any error (tag not found, anchor not set, etc.).
        """
        ...

    # ------------------------------------------------------------------ #
    #  Introspection                                                       #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def list_tags(self) -> Dict[str, str]:
        """
        Return a ``{tag: description}`` mapping of all registered entries.

        Useful for debugging, documentation generation, and CLI tooling.
        """
        ...

    @abstractmethod
    def info(self) -> str:
        """
        Return a formatted multi-line string summarising the manager's
        current configuration and all registered tags.
        """
        ...

    # ------------------------------------------------------------------ #
    #  Conflict resolution   (§7 — reserved; skeleton)                    #
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
