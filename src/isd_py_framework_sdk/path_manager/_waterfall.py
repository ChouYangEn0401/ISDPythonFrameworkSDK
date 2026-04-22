"""
Waterfall — ordered fallback chain for path resolution.

A ``Waterfall`` is a sequence of ``PathMode`` steps.  During resolution,
the manager attempts each step in order and returns the first path that
**exists on disk**.  If no step yields an existing path, a
``FileNotFoundError`` is raised, listing every attempted location.

Usage
-----
::

    from isd_py_framework_sdk.path_manager import Waterfall, PathMode

    # Custom waterfall
    wf = Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)
    path = pm.get("my_config", wf)

    # Pre-built waterfall
    path = pm.get("my_config", Waterfall.EXE_PREFER_BUNDLED)

Pre-built waterfalls
--------------------
``Waterfall.EXE_PREFER_BUNDLED``
    Read-optimized for deployed exes: try bundled data first, then
    the exe-side folder, then the project root.

``Waterfall.DEV_STANDARD``
    Development default: project root → raw absolute → cwd.

``Waterfall.EXE_WRITE_SAFE``
    Write-optimized for deployed exes: exe-side folder first, fall
    back to system temp if that is not writable/available.

``Waterfall.UNIVERSAL``
    Maximum compatibility: tries every anchor in a sensible order.
"""

from __future__ import annotations

from ._enums import PathMode


class Waterfall:
    """Ordered sequence of ``PathMode`` steps for fallback path resolution."""

    def __init__(self, *steps: PathMode) -> None:
        if not steps:
            raise ValueError("A Waterfall must contain at least one PathMode step.")
        self._steps: tuple[PathMode, ...] = steps

    # ------------------------------------------------------------------ #
    #  Public interface                                                    #
    # ------------------------------------------------------------------ #

    @property
    def steps(self) -> tuple[PathMode, ...]:
        """The ordered resolution steps (immutable)."""
        return self._steps

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
    #  Pre-built strategies (assigned after class definition)              #
    # ------------------------------------------------------------------ #

    #: Read-optimized for deployed exes.
    #: ``EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE``
    EXE_PREFER_BUNDLED: "Waterfall"

    #: Standard development fallback chain.
    #: ``PROJ_ABSOLUTE → ABSOLUTE → CWD``
    DEV_STANDARD: "Waterfall"

    #: Write-safe for deployed exes (no bundled-data write).
    #: ``EXE_ABSOLUTE → SYSTEM_TEMP``
    EXE_WRITE_SAFE: "Waterfall"

    #: Maximum compatibility — tries everything.
    #: ``EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE → CWD → SYSTEM_TEMP``
    UNIVERSAL: "Waterfall"


# Assign pre-built instances after the class is defined so that the
# type annotations above work correctly.
Waterfall.EXE_PREFER_BUNDLED = Waterfall(
    PathMode.EXE_INNER,
    PathMode.EXE_ABSOLUTE,
    PathMode.PROJ_ABSOLUTE,
)

Waterfall.DEV_STANDARD = Waterfall(
    PathMode.PROJ_ABSOLUTE,
    PathMode.ABSOLUTE,
    PathMode.CWD,
)

Waterfall.EXE_WRITE_SAFE = Waterfall(
    PathMode.EXE_ABSOLUTE,
    PathMode.SYSTEM_TEMP,
)

Waterfall.UNIVERSAL = Waterfall(
    PathMode.EXE_INNER,
    PathMode.EXE_ABSOLUTE,
    PathMode.PROJ_ABSOLUTE,
    PathMode.CWD,
    PathMode.SYSTEM_TEMP,
)
