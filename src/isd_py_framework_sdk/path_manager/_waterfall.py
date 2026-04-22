"""
Waterfall — ordered fallback chain for path resolution.

A ``Waterfall`` is a sequence of ``PathMode`` steps.  During resolution the
manager attempts each step in order and returns the first path that satisfies
a **validation check**.  By default:

- ``ResolveIntent.READ``  → the path must exist and be readable
- ``ResolveIntent.WRITE`` → the path's parent must exist and be writable
  (the path itself may not yet exist)

If you need custom validation, pass a ``check`` callable to the constructor.

If no step passes, a ``FileNotFoundError`` is raised that includes a
``WaterfallTrace`` listing every attempt — making debugging easy.

Usage
-----
::

    from isd_py_framework_sdk.path_manager import Waterfall, PathMode, ResolveIntent

    # Custom waterfall
    wf = Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)

    # Standard resolution (READ intent, raises on failure)
    path = pm.get("my_config", wf)

    # Write resolution
    path = pm.get("output_excel", Waterfall.ETL_OUTPUT, intent=ResolveIntent.WRITE)

    # Debug: see every attempt regardless of outcome
    path, trace = pm.get_with_trace("my_config", wf)
    for attempt in trace:
        print(attempt)

Pre-built Waterfalls
--------------------
Designed from real engineering scenarios:

+-------------------------------+----------------------------------------------+
| Constant                      | Use-case                                     |
+===============================+==============================================+
| DEV_STANDARD                  | Daily dev: project root → cwd               |
| DEV_WITH_USER_CONFIG          | Dev tools that honour ~/.config overrides   |
| PROD_READ                     | Deployed app reading config / assets        |
| PROD_WRITE                    | Deployed app writing logs / results         |
| EXE_PREFER_BUNDLED            | PyInstaller: bundled data → exe-side        |
| EXE_WRITE_SAFE                | PyInstaller writes: exe-side → sys temp     |
| ETL_INPUT                     | ETL pipeline: find input data               |
| ETL_OUTPUT                    | ETL pipeline: find/create output location   |
| CI_ARTIFACT                   | CI: proj root → cwd → sys temp             |
| UNIVERSAL                     | Maximum compatibility fallback              |
+-------------------------------+----------------------------------------------+
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

from ._enums import PathMode


# ------------------------------------------------------------------ #
#  Intent                                                             #
# ------------------------------------------------------------------ #

class ResolveIntent(Enum):
    """
    Whether we intend to **read** from or **write** to the resolved path.

    This affects the default validation check applied to each candidate:

    ``READ``
        The path must exist on disk.
    ``WRITE``
        The path's parent directory must exist (the file itself need not
        exist yet, and will be created by the caller).
    """

    READ  = auto()
    WRITE = auto()


# ------------------------------------------------------------------ #
#  Validation helpers                                                 #
# ------------------------------------------------------------------ #

def _check_exists(p: Path) -> bool:
    """Default READ check: path must exist."""
    return p.exists()


def _check_writable_location(p: Path) -> bool:
    """
    WRITE check: the path is writable, or an ancestor directory exists and
    is writable (meaning all intermediate directories can be created).

    Walks up the path hierarchy to the nearest existing ancestor rather than
    only checking the immediate parent.  This allows ``outputs/result.csv``
    to pass even when ``outputs/`` has not been created yet, as long as the
    project root (or temp dir) itself is writable.
    """
    if p.exists():
        return os.access(p, os.W_OK)
    candidate = p.parent
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:  # reached filesystem root without match
            return False
        candidate = parent
    return os.access(candidate, os.W_OK)


def _default_check(intent: ResolveIntent) -> Callable[[Path], bool]:
    if intent is ResolveIntent.READ:
        return _check_exists
    return _check_writable_location


# ------------------------------------------------------------------ #
#  Trace                                                              #
# ------------------------------------------------------------------ #

@dataclass
class Attempt:
    """
    Records one step in a ``Waterfall`` resolution attempt.

    Attributes
    ----------
    mode : PathMode
        The step that was tried.
    path : Path
        The candidate path that was evaluated (``Path("<error>")`` on exception).
    ok : bool
        Whether this step passed the validation check.
    reason : str
        Human-readable explanation (``"accepted"``, ``"check failed"``,
        or an exception message).
    """

    mode:   PathMode
    path:   Path
    ok:     bool
    reason: str

    def __str__(self) -> str:
        status = "✓" if self.ok else "✗"
        return f"  [{status}] {self.mode.name:<20} {self.path}  ({self.reason})"


class WaterfallTrace:
    """Collection of ``Attempt`` records from a single waterfall resolution."""

    def __init__(self, waterfall: "Waterfall", attempts: list[Attempt]) -> None:
        self._waterfall = waterfall
        self._attempts  = attempts

    @property
    def attempts(self) -> list[Attempt]:
        return list(self._attempts)

    @property
    def succeeded(self) -> bool:
        return any(a.ok for a in self._attempts)

    def __str__(self) -> str:
        lines = [f"WaterfallTrace for {self._waterfall}:"]
        lines.extend(str(a) for a in self._attempts)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return str(self)


# ------------------------------------------------------------------ #
#  Waterfall                                                          #
# ------------------------------------------------------------------ #

class Waterfall:
    """
    Ordered sequence of ``PathMode`` steps for fallback path resolution.

    Parameters
    ----------
    *steps : PathMode
        One or more ``PathMode`` values tried in order.
    check : callable, optional
        A custom ``(Path) -> bool`` predicate.  When provided it
        overrides the default intent-based check for every step.
    """

    def __init__(
        self,
        *steps: PathMode,
        check: Optional[Callable[[Path], bool]] = None,
    ) -> None:
        if not steps:
            raise ValueError("A Waterfall must contain at least one PathMode step.")
        self._steps: tuple[PathMode, ...] = steps
        self._check: Optional[Callable[[Path], bool]] = check

    # ------------------------------------------------------------------ #
    #  Public interface                                                    #
    # ------------------------------------------------------------------ #

    @property
    def steps(self) -> tuple[PathMode, ...]:
        """The ordered resolution steps (immutable)."""
        return self._steps

    def resolve(
        self,
        resolver: Callable[[PathMode], Path],
        *,
        intent: ResolveIntent = ResolveIntent.READ,
        with_trace: bool = False,
    ) -> "Path | tuple[Optional[Path], WaterfallTrace]":
        """
        Attempt each step using *resolver* and return the first passing path.

        Parameters
        ----------
        resolver :
            A callable ``(PathMode) -> Path`` supplied by the path manager.
            Keeping it external means ``Waterfall`` stays decoupled from
            the manager's internal state.
        intent :
            ``READ`` (default) or ``WRITE`` — controls the default check.
            Ignored when a custom ``check`` was passed to the constructor.
        with_trace :
            If ``True``, always return ``(path_or_None, WaterfallTrace)``
            instead of raising on failure.  The caller must handle
            ``path is None`` when all steps failed.

        Returns
        -------
        Path
            When *with_trace* is ``False`` and a step passes.
        (Path | None, WaterfallTrace)
            When *with_trace* is ``True``.

        Raises
        ------
        FileNotFoundError
            When *with_trace* is ``False`` and every step fails.
        """
        check = self._check or _default_check(intent)
        attempts: list[Attempt] = []

        for mode in self._steps:
            try:
                p = resolver(mode)
                ok = check(p)
                attempts.append(Attempt(mode, p, ok, "accepted" if ok else "check failed"))
                if ok:
                    if with_trace:
                        return p, WaterfallTrace(self, attempts)
                    return p
            except Exception as exc:
                attempts.append(Attempt(mode, Path("<error>"), False, str(exc)))

        trace = WaterfallTrace(self, attempts)
        if with_trace:
            return None, trace

        raise FileNotFoundError(
            f"Waterfall exhausted — no valid path found.\n{trace}"
        )

    # ------------------------------------------------------------------ #
    #  Dunder helpers                                                      #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        chain = " → ".join(s.name for s in self._steps)
        return f"Waterfall({chain})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Waterfall):
            return self._steps == other._steps
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._steps)

    # ------------------------------------------------------------------ #
    #  Pre-built strategies (assigned after class body)                   #
    # ------------------------------------------------------------------ #

    # -- Developer workstation ------------------------------------------

    #: Standard dev reading: project root first, fall back to cwd.
    DEV_STANDARD: "Waterfall"

    #: Dev tools that let ~/.config override project defaults
    #: (e.g. personal API keys, local DB credentials).
    DEV_WITH_USER_CONFIG: "Waterfall"

    # -- Production / deployed app ---------------------------------------

    #: Deployed app reading config, assets, reference data.
    #: Tries project root, then exe-side, then user config.
    PROD_READ: "Waterfall"

    #: Deployed app writing logs, outputs, caches.
    #: Tries exe-side folder, then user data dir, then system temp.
    PROD_WRITE: "Waterfall"

    # -- PyInstaller / frozen executable --------------------------------

    #: Frozen exe: prefer bundled-in data → shipped data next to exe → proj root.
    EXE_PREFER_BUNDLED: "Waterfall"

    #: Frozen exe writing outputs or cache: exe-side folder → user data → sys temp.
    EXE_WRITE_SAFE: "Waterfall"

    # -- ETL pipelines ---------------------------------------------------

    #: ETL input: find source data under proj root, then cwd, then sys temp
    #: (staging area).
    ETL_INPUT: "Waterfall"

    #: ETL output: write results to proj root output dir; if unavailable use
    #: user data dir; last resort sys temp so the pipeline never crashes silently.
    ETL_OUTPUT: "Waterfall"

    # -- CI / automated testing ------------------------------------------

    #: CI pipelines: proj root → cwd (workspace root) → sys temp (artefact dir).
    CI_ARTIFACT: "Waterfall"

    # -- Maximum compatibility -------------------------------------------

    #: Try everything in a sensible order.  Good for writing library code
    #: that must work in dev, deployed, and frozen envs without configuration.
    UNIVERSAL: "Waterfall"


# ------------------------------------------------------------------ #
#  Pre-built instances                                                #
# ------------------------------------------------------------------ #

# Developer workstation
Waterfall.DEV_STANDARD = Waterfall(
    PathMode.PROJ_ABSOLUTE,
    PathMode.CWD,
)

Waterfall.DEV_WITH_USER_CONFIG = Waterfall(
    PathMode.USER_CONFIG,
    PathMode.PROJ_ABSOLUTE,
    PathMode.CWD,
)

# Production
Waterfall.PROD_READ = Waterfall(
    PathMode.PROJ_ABSOLUTE,
    PathMode.EXE_ABSOLUTE,
    PathMode.USER_CONFIG,
)

Waterfall.PROD_WRITE = Waterfall(
    PathMode.EXE_ABSOLUTE,
    PathMode.USER_DATA,
    PathMode.SYSTEM_TEMP,
)

# PyInstaller / frozen
Waterfall.EXE_PREFER_BUNDLED = Waterfall(
    PathMode.EXE_INNER,
    PathMode.EXE_ABSOLUTE,
    PathMode.PROJ_ABSOLUTE,
)

Waterfall.EXE_WRITE_SAFE = Waterfall(
    PathMode.EXE_ABSOLUTE,
    PathMode.USER_DATA,
    PathMode.SYSTEM_TEMP,
)

# ETL
Waterfall.ETL_INPUT = Waterfall(
    PathMode.PROJ_ABSOLUTE,
    PathMode.CWD,
    PathMode.SYSTEM_TEMP,
)

Waterfall.ETL_OUTPUT = Waterfall(
    PathMode.PROJ_ABSOLUTE,
    PathMode.USER_DATA,
    PathMode.SYSTEM_TEMP,
)

# CI
Waterfall.CI_ARTIFACT = Waterfall(
    PathMode.PROJ_ABSOLUTE,
    PathMode.CWD,
    PathMode.SYSTEM_TEMP,
)

# Universal
Waterfall.UNIVERSAL = Waterfall(
    PathMode.EXE_INNER,
    PathMode.EXE_ABSOLUTE,
    PathMode.PROJ_ABSOLUTE,
    PathMode.CWD,
    PathMode.USER_DATA,
    PathMode.SYSTEM_TEMP,
)

