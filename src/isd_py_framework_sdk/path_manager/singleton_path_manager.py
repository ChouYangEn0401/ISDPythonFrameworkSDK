"""
SingletonPathManager — the reference implementation of ``IPathManager``.

A thread-safe singleton that centralizes all path bookkeeping for a
project.  Every module, sub-package, and worker thread shares the same
instance, so registering a path once at startup makes it accessible
everywhere without re-computing relative paths.

一個線程安全的單例，集中管理專案的所有路徑紀錄。
每個模組、子套件和工作執行緒共享相同實例，
因此在啟動時註冊一次路徑即可在各處存取，無需重複計算相對路徑。

Quick start
-----------
```python
    from isd_py_framework_sdk.path_manager import (
        SingletonPathManager, PathMode, Waterfall,
    )

    pm = SingletonPathManager()

    # Configure once at entry point (e.g. main.py / app.py)
    pm.set_proj_root(__file__, levels_up=1)   # go 1 level up from main.py

    pm.register("data_in",   "data/inputs",     description="Raw input files")
    pm.register("data_out",  "data/outputs",    description="Generated outputs")
    pm.register("error_log", "logs/error.log",  description="Runtime error log")

    # Read from anywhere in the codebase
    from isd_py_framework_sdk.path_manager import SingletonPathManager, PathMode
    pm = SingletonPathManager()                   # same singleton instance

    path = pm.get("data_in")                      # absolute Path
    rel  = pm.get("data_in", PathMode.PROJ_RELATIVE)  # relative Path

    # Waterfall: first existing path wins
    path = pm.get("config", Waterfall.UNIVERSAL)
```
Quick start example: 
The above program demonstrates how to obtain a `SingletonPathManager` instance, 
set the project root at the program entry point, register the path, and obtain 
the absolute or relative path at any point in the program using `pm.get(...)`; 
`Waterfall` will return the first existing path.

快速上手示例：上述程式示範如何取得 `SingletonPathManager` 實例、在程式入口設定專案根、註冊路徑，
並在程式任意位置以 `pm.get(...)` 取得絕對或相對路徑；`Waterfall` 會回傳第一個存在的路徑。

Multiprocessing note
--------------------
Each OS process has its own singleton.  If you launch sub-processes via
``multiprocessing``, configure the path manager in each child process
separately (or serialise the registry with ``to_dict()`` / ``from_dict()``
in a future release — see ``dev_plan.md`` §6).

每個作業系統程序都有自己的單例。
如果使用 `multiprocessing` 啟動子程序，請在每個子程序中分別設定路徑管理器；
或在未來以 `to_dict()` / `from_dict()` 序列化註冊表還原（參見 `dev_plan.md` §6）。

Threads share the same process memory, so the singleton is naturally
shared across threads.

執行緒共享程序記憶體，因此單例會自然地在執行緒間共享。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Union

from .interface import IPathManager
from ._enums import PathMode
from ._waterfall import Waterfall
from ._conflict import ConflictStrategy, IncrementSuffixStrategy
from ._registry import PathEntry, PathRegistry
from ._resolver import EnvironmentResolver
from src.isd_py_framework_sdk.base.Singleton import SingletonMetaclass


class SingletonPathManager(IPathManager, metaclass=SingletonMetaclass):
    """
    Thread-safe singleton path manager.
    """

    # ------------------------------------------------------------------ #
    #  Singleton initialisation (called exactly once by SingletonMetaclass)#
    # ------------------------------------------------------------------ #

    def _initialize_manager(self) -> None:
        self._registry: PathRegistry = PathRegistry()
        self._proj_root: Optional[Path] = None
        self._default_conflict_strategy: ConflictStrategy = IncrementSuffixStrategy()

    # ------------------------------------------------------------------ #
    #  Configuration                                                       #
    # ------------------------------------------------------------------ #

    def set_proj_root(
        self,
        path: Union[Path, str],
        *,
        levels_up: int = 0,
    ) -> None:
        """
        Set the project-root directory used for ``PROJ_*`` path modes.

        Parameters
        ----------
        path :
            A directory path **or** a ``__file__`` value from any module.
            If *path* points to a file, its parent directory is used as
            the starting point.
        levels_up :
            How many parent levels to ascend from the resolved starting
            point.

            Example — caller file is at ``project/src/pkg/config.py``
            and the desired root is ``project/``::

                pm.set_proj_root(__file__, levels_up=2)
        """
        root = Path(path).resolve()
        if root.is_file():
            root = root.parent
        for _ in range(levels_up):
            root = root.parent
        self._proj_root = root

    def set_default_conflict_strategy(self, strategy: ConflictStrategy) -> None:
        """
        Replace the default conflict strategy used when ``resolve_conflict``
        is called without an explicit *strategy* argument.
        """
        self._default_conflict_strategy = strategy

    # ------------------------------------------------------------------ #
    #  Registry                                                            #
    # ------------------------------------------------------------------ #

    def register(
        self,
        tag: str,
        path: Union[Path, str],
        *,
        anchor: PathMode = PathMode.PROJ_RELATIVE,
        description: str = "",
    ) -> None:
        self._registry.add(
            PathEntry(
                tag=tag,
                stored_path=Path(path),
                anchor=anchor,
                description=description,
            )
        )

    def unregister(self, tag: str) -> None:
        self._registry.remove(tag)

    def has(self, tag: str) -> bool:
        return self._registry.has(tag)

    # ------------------------------------------------------------------ #
    #  Resolution                                                          #
    # ------------------------------------------------------------------ #

    def get(
        self,
        tag: str,
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> Path:
        entry = self._registry.get(tag)
        if isinstance(mode, Waterfall):
            return self._resolve_waterfall(entry, mode)
        return self._resolve(entry, mode)

    def exists(
        self,
        tag: str,
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> bool:
        try:
            return self.get(tag, mode).exists()
        except (KeyError, FileNotFoundError, RuntimeError, ValueError):
            return False

    # Convenience aliases that express intent at the call site
    def getdir(
        self,
        tag: str,
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> Path:
        """Alias for ``get()``; signals that the result is expected to be a directory."""
        return self.get(tag, mode)

    def getfile(
        self,
        tag: str,
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> Path:
        """Alias for ``get()``; signals that the result is expected to be a file."""
        return self.get(tag, mode)

    # ------------------------------------------------------------------ #
    #  Introspection                                                       #
    # ------------------------------------------------------------------ #

    def list_tags(self) -> Dict[str, str]:
        return {
            tag: entry.description
            for tag, entry in self._registry.all_entries().items()
        }

    def info(self) -> str:
        """
        Return a formatted multi-line diagnostic string covering environment
        detection, configured anchors, and the full tag registry.
        """
        is_pyinstaller = EnvironmentResolver.is_pyinstaller()
        exe_side = EnvironmentResolver.exe_side_root()
        sys_temp = EnvironmentResolver.system_temp_root()
        cwd = EnvironmentResolver.cwd()

        lines = [
            "=== SingletonPathManager ===",
            f"  pyinstaller : {is_pyinstaller}",
            f"  proj_root   : {self._proj_root or '(not set — call set_proj_root())'}",
            f"  exe_side    : {exe_side}",
        ]
        if is_pyinstaller:
            lines.append(f"  exe_inner   : {EnvironmentResolver.exe_inner_root()}")
        lines += [
            f"  system_temp : {sys_temp}",
            f"  cwd         : {cwd}",
            "",
            f"  Registered tags ({len(self._registry.all_entries())}):",
        ]
        for tag, entry in self._registry.all_entries().items():
            lines.append(
                f"    [{tag!r:<20}]  anchor={entry.anchor.name:<14}  "
                f"path={entry.stored_path}"
                + (f"  # {entry.description}" if entry.description else "")
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    #  Conflict resolution   (§7 — partial implementation)                #
    # ------------------------------------------------------------------ #

    def resolve_conflict(
        self,
        tag: str,
        *,
        strategy: Optional[ConflictStrategy] = None,
        mode: PathMode = PathMode.ABSOLUTE,
    ) -> Path:
        target = self.get(tag, mode)
        _strategy = strategy or self._default_conflict_strategy
        if target.exists():
            resolved = _strategy.resolve(target)
            print(_strategy.conflict_info(target, resolved))
            return resolved
        return target  ## will allow user to rebuild path or file i think ??

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _to_absolute(self, entry: PathEntry) -> Path:
        """
        Convert ``entry.stored_path + entry.anchor`` → canonical absolute Path.

        This is the single source of truth for understanding how a stored
        relative path maps to an actual location on disk.
        """
        p = entry.stored_path
        anchor = entry.anchor

        if anchor == PathMode.ABSOLUTE:
            return p.resolve()

        if anchor in (PathMode.PROJ_RELATIVE, PathMode.PROJ_ABSOLUTE):
            if self._proj_root is None:
                raise RuntimeError(
                    f"Tag '{entry.tag}' uses a PROJ_* anchor but "
                    "set_proj_root() has not been called on this manager."
                )
            return (self._proj_root / p).resolve()

        if anchor in (PathMode.EXE_RELATIVE, PathMode.EXE_ABSOLUTE):
            return (EnvironmentResolver.exe_side_root() / p).resolve()

        if anchor == PathMode.EXE_INNER:
            return (EnvironmentResolver.exe_inner_root() / p).resolve()

        if anchor == PathMode.SYSTEM_TEMP:
            return (EnvironmentResolver.system_temp_root() / p).resolve()

        if anchor == PathMode.CWD:
            return (EnvironmentResolver.cwd() / p).resolve()

        raise ValueError(f"Unknown anchor PathMode: {anchor!r}")

    def _resolve(self, entry: PathEntry, mode: PathMode) -> Path:
        """
        Resolve *entry* and express the result in the requested *mode*.

        For absolute-like modes (``ABSOLUTE``, ``PROJ_ABSOLUTE``,
        ``EXE_ABSOLUTE``, ``EXE_INNER``, ``SYSTEM_TEMP``) the result is
        always an absolute path.

        For relative modes (``PROJ_RELATIVE``, ``EXE_RELATIVE``, ``CWD``)
        the result is a relative ``Path`` expressed from the corresponding
        anchor.
        """
        absolute = self._to_absolute(entry)

        if mode == PathMode.ABSOLUTE:
            return absolute

        if mode == PathMode.PROJ_RELATIVE:
            if self._proj_root is None:
                raise RuntimeError("set_proj_root() has not been called.")
            try:
                return absolute.relative_to(self._proj_root)
            except ValueError:
                raise ValueError(
                    f"Tag '{entry.tag}': resolved path '{absolute}' is not "
                    f"inside proj_root '{self._proj_root}'.  "
                    "Cannot express as PROJ_RELATIVE."
                )

        if mode == PathMode.PROJ_ABSOLUTE:
            if self._proj_root is None:
                raise RuntimeError("set_proj_root() has not been called.")
            return (self._proj_root / entry.stored_path).resolve()

        if mode == PathMode.EXE_RELATIVE:
            exe = EnvironmentResolver.exe_side_root()
            try:
                return absolute.relative_to(exe)
            except ValueError:
                # Path is outside exe_side_root; return stored_path as a
                # best-effort relative representation.
                return entry.stored_path

        if mode == PathMode.EXE_ABSOLUTE:
            return (EnvironmentResolver.exe_side_root() / entry.stored_path).resolve()

        if mode == PathMode.EXE_INNER:
            return (EnvironmentResolver.exe_inner_root() / entry.stored_path).resolve()

        if mode == PathMode.SYSTEM_TEMP:
            return (EnvironmentResolver.system_temp_root() / entry.stored_path).resolve()

        if mode == PathMode.CWD:
            try:
                return absolute.relative_to(EnvironmentResolver.cwd())
            except ValueError:
                return absolute  # falls back to absolute if not under cwd

        raise ValueError(f"Unknown PathMode: {mode!r}")

    def _mode_to_absolute(self, entry: PathEntry, mode: PathMode) -> Path:
        """
        Construct an absolute path by combining *mode*'s anchor directory
        with ``entry.stored_path``.

        Used exclusively by ``_resolve_waterfall`` where we always need an
        absolute path to check ``.exists()``.

        Unlike ``_resolve``, this method ignores ``entry.anchor`` and
        always interprets ``entry.stored_path`` as relative to whichever
        anchor *mode* implies.
        """
        p = entry.stored_path

        if mode == PathMode.ABSOLUTE:
            return p.resolve()

        if mode in (PathMode.PROJ_RELATIVE, PathMode.PROJ_ABSOLUTE):
            if self._proj_root is None:
                raise RuntimeError("set_proj_root() has not been called.")
            return (self._proj_root / p).resolve()

        if mode in (PathMode.EXE_RELATIVE, PathMode.EXE_ABSOLUTE):
            return (EnvironmentResolver.exe_side_root() / p).resolve()

        if mode == PathMode.EXE_INNER:
            return (EnvironmentResolver.exe_inner_root() / p).resolve()

        if mode == PathMode.SYSTEM_TEMP:
            return (EnvironmentResolver.system_temp_root() / p).resolve()

        if mode == PathMode.CWD:
            return (EnvironmentResolver.cwd() / p).resolve()

        raise ValueError(f"Unknown PathMode in waterfall step: {mode!r}")

    def _resolve_waterfall(self, entry: PathEntry, waterfall: Waterfall) -> Path:
        """
        Try each step of *waterfall* in order; return the first absolute
        path that exists on disk.

        Raises ``FileNotFoundError`` (with full diagnostic info) if no
        step yields an existing path.
        """
        tried: list[str] = []
        for step in waterfall.steps:
            try:
                candidate = self._mode_to_absolute(entry, step)
                if candidate.exists():
                    return candidate
                tried.append(f"{step.name}={candidate}")
            except (RuntimeError, ValueError) as exc:
                tried.append(f"{step.name}=<unavailable: {exc}>")

        raise FileNotFoundError(
            f"Tag '{entry.tag}': no path found via {waterfall}.\n"
            f"  Tried: {', '.join(tried)}"
        )
