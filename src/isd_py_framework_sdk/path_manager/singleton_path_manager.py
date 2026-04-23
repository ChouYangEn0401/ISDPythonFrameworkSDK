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

import threading
from pathlib import Path
from typing import Dict, Optional, Union

from .interface import IPathManager
from ._enums import PathMode
from ._waterfall import Waterfall, ResolveIntent, WaterfallTrace
from ._conflict import ConflictStrategy, IncrementSuffixStrategy
from ._registry import PathEntry, PathRegistry
from ._resolver import EnvironmentResolver
from ._meta import SingletonABCMeta


class SingletonPathManager(IPathManager, metaclass=SingletonABCMeta):
    """
    Thread-safe singleton path manager.

    Design contract
    ---------------
    * ``register(tag, rel_path, anchor)``
        *anchor* is **required** — you must declare where this path lives
        (``PathMode.PROJ_ABSOLUTE``, ``PathMode.USER_CONFIG``, etc.).
        The stored *rel_path* is always relative to that anchor's base
        directory, except when ``anchor=PathMode.ABSOLUTE`` (store as-is).

    * ``get(tag)``
        Returns the **absolute** path, resolved from the registered anchor.
        No hidden re-anchoring — what you declared at registration is what
        you get.

    * ``get(tag, Waterfall.XYZ)``
        Cross-environment override: tries each ``PathMode`` in the waterfall
        in order (combining that mode's base directory with the stored
        relative path), returning the first that satisfies *intent*.
        Use this for PyInstaller / prod / dev fallback chains.

    * ``as_relative(tag, base)``
        Re-expresses the already-resolved absolute path as relative to
        *base*'s directory — for display, logging, or relative imports.
        Does NOT override the registration anchor.
    """

    # ------------------------------------------------------------------ #
    #  Singleton initialisation (called exactly once)                     #
    # ------------------------------------------------------------------ #

    def _initialize_manager(self) -> None:
        self._app_name: str = "app"
        self._proj_root: Optional[Path] = None
        self._registry: PathRegistry = PathRegistry()
        self._anchor_remaps: dict[PathMode, PathMode] = {}
        self._default_conflict_strategy: ConflictStrategy = IncrementSuffixStrategy()
        self._lock = threading.Lock()

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
        Set the project-root directory used for ``PROJ_*`` anchors.

        Pass a ``__file__`` value and use *levels_up* to ascend to the
        actual project root::

            pm.set_proj_root(__file__, levels_up=2)   # from src/pkg/main.py → project/
        """
        root = Path(path).resolve()
        if root.is_file():
            root = root.parent
        for _ in range(levels_up):
            root = root.parent
        self._proj_root = root

    def set_default_conflict_strategy(self, strategy: ConflictStrategy) -> None:
        """Replace the strategy used by ``resolve_conflict`` when no explicit one is given."""
        self._default_conflict_strategy = strategy

    # ------------------------------------------------------------------ #
    #  Anchor remapping                                                    #
    # ------------------------------------------------------------------ #

    def remap_anchor(self, from_mode: PathMode, to_mode: PathMode) -> None:
        """
        Globally redirect all tags registered under *from_mode* to resolve
        against *to_mode* instead — without changing any ``register()`` call.

        Typical use: one-line switch from dev layout to PyInstaller layout::

            import sys
            pm = SingletonPathManager()
            if getattr(sys, 'frozen', False):
                pm.remap_anchor(PathMode.PROJ_ABSOLUTE, PathMode.EXE_INNER)

        Every subsequent ``get()`` call for tags registered with
        ``PROJ_ABSOLUTE`` will resolve against ``sys._MEIPASS`` instead of
        the project root — no edits to ``register()`` calls required.

        Calling again with the same *from_mode* silently overwrites the remap.
        Remove with :meth:`remove_anchor_remap` or :meth:`clear_anchor_remaps`.

        一行切換開發/打包環境，不需更改任何 register() 呼叫：:

            if getattr(sys, 'frozen', False):
                pm.remap_anchor(PathMode.PROJ_ABSOLUTE, PathMode.EXE_INNER)
        """
        with self._lock:
            self._anchor_remaps[from_mode] = to_mode

    def remove_anchor_remap(self, from_mode: PathMode) -> None:
        """
        Remove the anchor remap for *from_mode*.  No-op if not set.

        移除 *from_mode* 的 anchor remap；若未設定則不報錯。
        """
        with self._lock:
            self._anchor_remaps.pop(from_mode, None)

    def clear_anchor_remaps(self) -> None:
        """
        Remove ALL active anchor remaps.

        清除所有 anchor remap。
        """
        with self._lock:
            self._anchor_remaps.clear()

    def set_app_name(self, name: str) -> None:
        """
        Set the application name used when resolving ``USER_*`` anchors.

        Affects ``USER_CONFIG``, ``USER_DATA``, and ``USER_CACHE`` directory
        names (e.g. ``~/.config/<name>``).  Defaults to ``"app"``.
        """
        self._app_name = name

    # ------------------------------------------------------------------ #
    #  Registry                                                            #
    # ------------------------------------------------------------------ #

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

        *anchor* is **required** — it declares which base directory
        *path* is relative to:

        ==================  ===========================================
        ``PathMode``        Base directory
        ==================  ===========================================
        ``PROJ_ABSOLUTE``   ``proj_root`` (set via ``set_proj_root``)
        ``EXE_ABSOLUTE``    Directory containing the running exe/script
        ``EXE_INNER``       ``sys._MEIPASS`` (PyInstaller bundle)
        ``USER_CONFIG``     ``~/.config/<app_name>`` (or OS equivalent)
        ``USER_DATA``       ``~/.local/share/<app_name>``
        ``USER_CACHE``      ``~/.cache/<app_name>``
        ``SYSTEM_TEMP``     System temp directory
        ``CWD``             Current working directory at call time
        ``ABSOLUTE``        *path* is already an absolute path
        ==================  ===========================================

        Re-registering an existing *tag* silently overwrites it.
        """
        with self._lock:
            self._registry.add(
                PathEntry(
                    tag=tag,
                    stored_path=Path(path),
                    anchor=anchor,
                    description=description,
                )
            )

    def unregister(self, tag: str) -> None:
        """Remove *tag* from the registry.  Raises ``KeyError`` if absent."""
        self._registry.remove(tag)

    def has(self, tag: str) -> bool:
        """Return ``True`` if *tag* is currently registered."""
        return self._registry.has(tag)

    # ------------------------------------------------------------------ #
    #  Resolution                                                          #
    # ------------------------------------------------------------------ #

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
            Always returns an absolute ``Path``.

        ``get(tag, Waterfall.XYZ)``
            Tries each mode in the waterfall in order (combining that
            mode's base dir with the stored relative path).  Returns the
            first path that satisfies *intent*:

            * ``ResolveIntent.READ``  — the path must exist on disk
            * ``ResolveIntent.WRITE`` — the path's *parent* must exist
              and be writable (the file itself need not exist yet)

            Raises ``FileNotFoundError`` if no step succeeds.
        """
        entry = self._registry.get(tag)
        if waterfall is not None:
            return self._resolve_waterfall(entry, waterfall, intent=intent)
        return self._to_absolute(entry)

    def as_relative(self, tag: str, base: PathMode) -> Path:
        """
        Re-express the resolved absolute path for *tag* as relative to
        *base*'s anchor directory.

        Use this for display, logging, or when you need a path relative
        to a known root.  Does **not** override the registered anchor.

        Raises ``ValueError`` if the resolved path is not inside *base*'s
        directory.
        """
        absolute = self._to_absolute(self._registry.get(tag))
        base_dir = self._anchor_dir(base)
        try:
            return absolute.relative_to(base_dir)
        except ValueError:
            raise ValueError(
                f"Tag '{tag}': resolved path '{absolute}' is not inside "
                f"{base.name} directory '{base_dir}'."
            )

    def get_with_trace(
        self,
        tag: str,
        waterfall: Waterfall,
        *,
        intent: ResolveIntent = ResolveIntent.READ,
    ) -> "tuple[Optional[Path], WaterfallTrace]":
        """
        Like ``get(tag, waterfall)`` but **never raises**.

        Returns ``(path, trace)`` where *path* is ``None`` on failure.
        Use this to debug waterfall resolution or build conditional logic
        without try/except.
        """
        entry = self._registry.get(tag)
        resolver = lambda mode: self._apply_anchor(entry.stored_path, mode)
        return waterfall.resolve(resolver, intent=intent, with_trace=True)  # type: ignore[return-value]

    def exists(self, tag: str) -> bool:
        """
        Non-raising existence check.

        Returns ``True`` if the resolved path exists on disk.
        Returns ``False`` for any error (tag not found, anchor not set, etc.).
        """
        try:
            return self.get(tag).exists()
        except (KeyError, FileNotFoundError, RuntimeError, ValueError):
            return False

    # ------------------------------------------------------------------ #
    #  Introspection                                                       #
    # ------------------------------------------------------------------ #

    def list_tags(self) -> Dict[str, str]:
        """Return ``{tag: description}`` for all registered entries."""
        return {
            tag: entry.description
            for tag, entry in self._registry.all_entries().items()
        }

    def info(self) -> str:
        """Return a diagnostic string: environment state + full tag registry."""
        is_pyinstaller = EnvironmentResolver.is_pyinstaller()
        lines = [
            "=== SingletonPathManager ===",
            f"  pyinstaller : {is_pyinstaller}",
            f"  proj_root   : {self._proj_root or '(not set — call set_proj_root())'}",
            f"  app_name    : {self._app_name}",
            f"  exe_side    : {EnvironmentResolver.exe_side_root()}",
        ]
        if is_pyinstaller:
            lines.append(f"  exe_inner   : {EnvironmentResolver.exe_inner_root()}")
        lines += [
            f"  system_temp : {EnvironmentResolver.system_temp_root()}",
            f"  cwd         : {EnvironmentResolver.cwd()}",
        ]
        if self._anchor_remaps:
            lines.append("")
            lines.append(f"  Anchor remaps ({len(self._anchor_remaps)} active):")
            for frm, to in self._anchor_remaps.items():
                lines.append(f"    {frm.name} → {to.name}")
        lines += [
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
    #  Conflict resolution                                                 #
    # ------------------------------------------------------------------ #

    def resolve_conflict(
        self,
        tag: str,
        *,
        strategy: Optional[ConflictStrategy] = None,
    ) -> Path:
        """
        Return a safe write path for *tag*, applying a conflict strategy
        if the target already exists.

        If the file does not exist, the registered path is returned as-is.
        """
        target = self.get(tag)
        _strategy = strategy or self._default_conflict_strategy
        if target.exists():
            resolved = _strategy.resolve(target)
            print(_strategy.conflict_info(target, resolved))
            return resolved
        return target

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _anchor_dir(self, mode: PathMode) -> Path:
        """
        Return the base directory for a given *mode*.

        This is the directory that ``register()``'s relative path is
        appended to when *mode* is used as an anchor.
        """
        if mode in (PathMode.PROJ_RELATIVE, PathMode.PROJ_ABSOLUTE):
            if self._proj_root is None:
                raise RuntimeError(
                    "A PROJ_* anchor requires set_proj_root() to be called first."
                )
            return self._proj_root

        if mode in (PathMode.EXE_RELATIVE, PathMode.EXE_ABSOLUTE):
            return EnvironmentResolver.exe_side_root()

        if mode == PathMode.EXE_INNER:
            return EnvironmentResolver.exe_inner_root()

        if mode == PathMode.SYSTEM_TEMP:
            return EnvironmentResolver.system_temp_root()

        if mode == PathMode.CWD:
            return EnvironmentResolver.cwd()

        if mode == PathMode.SCRIPT_DIR:
            return EnvironmentResolver.script_dir()

        if mode == PathMode.USER_HOME:
            return EnvironmentResolver.user_home()

        if mode == PathMode.USER_CONFIG:
            return EnvironmentResolver.user_config(self._app_name)

        if mode == PathMode.USER_DATA:
            return EnvironmentResolver.user_data(self._app_name)

        if mode == PathMode.USER_CACHE:
            return EnvironmentResolver.user_cache(self._app_name)

        if mode == PathMode.VIRTUAL_ENV:
            return EnvironmentResolver.virtual_env()

        raise ValueError(
            f"PathMode.{mode.name} has no single base directory "
            "(use ABSOLUTE or PACKAGE_RESOURCE only via _apply_anchor)."
        )

    def _apply_anchor(self, stored_path: Path, anchor: PathMode) -> Path:
        """
        Canonical resolution: combine *anchor*'s base directory with
        *stored_path* → absolute Path.

        Used by both ``_to_absolute`` (registered anchor) and the waterfall
        resolver (override anchor).  Respects any active anchor remaps.
        """
        # Apply any global anchor remap installed by remap_anchor().
        # 套用 remap_anchor() 安裝的全域重定向（若未設定則使用原始 anchor）。
        anchor = self._anchor_remaps.get(anchor, anchor)

        if anchor == PathMode.ABSOLUTE:
            return stored_path.resolve()

        if anchor == PathMode.PACKAGE_RESOURCE:
            # Caller is expected to provide a pre-resolved resource path.
            return stored_path.resolve()

        return (self._anchor_dir(anchor) / stored_path).resolve()

    def _to_absolute(self, entry: PathEntry) -> Path:
        """Resolve *entry* using its registered anchor → canonical absolute Path."""
        return self._apply_anchor(entry.stored_path, entry.anchor)

    def _resolve_waterfall(
        self,
        entry: PathEntry,
        waterfall: Waterfall,
        *,
        intent: ResolveIntent = ResolveIntent.READ,
    ) -> Path:
        """Delegate to Waterfall.resolve(), mapping each PathMode → absolute Path."""
        resolver = lambda mode: self._apply_anchor(entry.stored_path, mode)
        return waterfall.resolve(resolver, intent=intent)  # type: ignore[return-value]
