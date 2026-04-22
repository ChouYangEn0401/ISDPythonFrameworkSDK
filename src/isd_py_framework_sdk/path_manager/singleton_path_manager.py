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
        levels_up :
            How many parent levels to ascend from the resolved starting
            point.

        """
        root = Path(path).resolve()
        if root.is_file():
            root = root.parent
        for _ in range(levels_up):
            root = root.parent
        self._proj_root = root

    def set_default_conflict_strategy(self, strategy: ConflictStrategy) -> None:
        self._default_conflict_strategy = strategy

    # ------------------------------------------------------------------ #
    #  Registry                                                            #
    # ------------------------------------------------------------------ #

    def register(
        self,
        tag: str,
        path: Union[Path, str],
        *,
        description: str = "",
    ) -> None:
        self._registry.add(
            PathEntry(
                tag=tag,
                stored_path=Path(path),
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
        return self.get(tag, mode)

    def getfile(
        self,
        tag: str,
        mode: Union[PathMode, Waterfall] = PathMode.ABSOLUTE,
    ) -> Path:
        return self.get(tag, mode)

    # ------------------------------------------------------------------ #
    #  Introspection                                                       #
    # ------------------------------------------------------------------ #

    def list_tags(self) -> Dict[str, str]:
        return {
            tag: entry.description
            for tag, entry in self._registry.all_entries().items()
        }


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


    def _resolve(self, entry: PathEntry, mode: PathMode) -> Path:
        ...

    def _resolve_waterfall(self, entry: PathEntry, waterfall: Waterfall) -> Path:
        ...
