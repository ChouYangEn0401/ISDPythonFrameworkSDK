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

Pre-built Waterfalls
--------------------
Designed from real engineering scenarios:

+-------------------------------+----------------------------------------------+
| Constant                      | Use-case                                     |
+===============================+==============================================+
| DEV_STANDARD                  | Daily dev: project root → cwd               |
| DEV_WITH_USER_CONFIG          | Dev tools that honour ~/.config overrides   |
| EXE_PREFER_BUNDLED            | PyInstaller: bundled data → exe-side        |
| CI_ARTIFACT                   | CI: proj root → cwd → sys temp             |
| UNIVERSAL                     | Maximum compatibility fallback              |
+-------------------------------+----------------------------------------------+
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
    #  Pre-built strategies (assigned after class body)                   #
    # ------------------------------------------------------------------ #

    # -- Developer workstation ------------------------------------------

    #: Standard dev reading: project root first, fall back to cwd.
    DEV_STANDARD: "Waterfall"

    #: Dev tools that let ~/.config override project defaults
    #: (e.g. personal API keys, local DB credentials).
    DEV_WITH_USER_CONFIG: "Waterfall"

    # -- PyInstaller / frozen executable --------------------------------

    #: Frozen exe: prefer bundled-in data → shipped data next to exe → proj root.
    EXE_PREFER_BUNDLED: "Waterfall"

    #: Standard development fallback chain.
    #: ``PROJ_ABSOLUTE → ABSOLUTE → CWD``
    DEV_STANDARD: "Waterfall"

    #: Write-safe for deployed exes (no bundled-data write).
    #: ``EXE_ABSOLUTE → SYSTEM_TEMP``
    EXE_WRITE_SAFE: "Waterfall"

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


# PyInstaller / frozen
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

