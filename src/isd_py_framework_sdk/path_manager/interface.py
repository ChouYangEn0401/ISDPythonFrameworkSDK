from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Union

from ._enums import PathMode
from ._waterfall import Waterfall
from ._conflict import ConflictStrategy


class IPathManager(ABC):
    """Abstract base class for all path managers in the ISD framework."""

    @abstractmethod
    def set_proj_root(
        self,
        path: Union[Path, str],
        *,
        levels_up: int = 0,
    ) -> None:
        ...

    @abstractmethod
    def register(
        self,
        tag: str,
        path: Union[Path, str],
        *,
        description: str = "",
    ) -> None:
        """
        Register *path* under *tag*.

        Parameters
        ----------
        tag :
            Unique string identifier.
        path :
            The path to store.
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

    @abstractmethod
    def list_tags(self) -> Dict[str, str]:
        """
        Return a ``{tag: description}`` mapping of all registered entries.
        """
        ...

    @abstractmethod
    def resolve_conflict(
        self,
        tag: str,
        strategy: Optional[ConflictStrategy] = None,
    ) -> Path:
        """
        Compute a safe write path for *tag*, applying *strategy* if the
        resolved path already exists on disk.
        Returns
        -------
        Path
            The path the caller should write to (may differ from the
            resolved path when a conflict was detected).
        """
        ...
