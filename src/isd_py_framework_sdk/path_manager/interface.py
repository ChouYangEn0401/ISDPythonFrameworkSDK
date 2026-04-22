"""
IPathManager — abstract interface for path managers.

Design contract
---------------
* ``set_proj_root`` — configure the project-root anchor
* ``register(tag, path, anchor)`` — anchor is REQUIRED; declares where
  the path lives so resolution is always unambiguous
* ``get(tag)`` — resolve to absolute Path using registered anchor
* ``get(tag, Waterfall)`` — cross-environment override via fallback chain
* ``as_relative(tag, base)`` — re-express absolute path relative to base
* ``get_with_trace`` — debugging: never raises, returns trace
* ``exists`` — non-raising existence check
* ``list_tags`` / ``info`` — introspect the registry (debugging / documentation)
* ``resolve_conflict`` — compute safe write path
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

from ._enums import PathMode
from ._waterfall import Waterfall, ResolveIntent, WaterfallTrace
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
        """Set the project-root directory used for ``PROJ_*`` anchors."""
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
        intent: ResolveIntent = ResolveIntent.READ,
    ) -> Path:
        """
        Return the absolute path for *tag*.

        ``get(tag)``
            Resolves using the anchor declared at registration.

        ``get(tag, Waterfall.XYZ)``
            Cross-environment override: tries each PathMode in the
            waterfall, returning the first satisfying *intent*.
        """
        ...

    @abstractmethod
    def as_relative(self, tag: str, base: PathMode) -> Path:
        """
        Re-express the resolved absolute path for *tag* as relative to
        *base*'s anchor directory.

        Use for display / logging.  Does NOT override the registration anchor.
        Raises ``ValueError`` if the resolved path is not inside *base*'s dir.
        """
        ...

    @abstractmethod
    def get_with_trace(
        self,
        tag: str,
        waterfall: Waterfall,
        *,
        intent: ResolveIntent = ResolveIntent.READ,
    ) -> "tuple[Optional[Path], WaterfallTrace]":
        """Return ``(path_or_None, trace)`` without raising on failure."""
        ...

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
    ) -> Path:
        """
        Return a safe write path for *tag*, applying *strategy* if the target
        already exists.  Uses the manager's default strategy when *strategy*
        is ``None`` (``IncrementSuffixStrategy`` out of the box).
        """
        ...

