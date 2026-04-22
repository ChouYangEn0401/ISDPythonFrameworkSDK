"""
Waterfall — ordered fallback chain for path resolution.

Pre-built waterfalls
--------------------
``Waterfall.EXE_PREFER_BUNDLED``
    Read-optimized for deployed exes: try bundled data first, then
    the exe-side folder, then the project root.

``Waterfall.DEV_STANDARD``

``Waterfall.EXE_WRITE_SAFE``
    Write-optimized for deployed exes: exe-side folder first, fall
    back to system temp if that is not writable/available.

``Waterfall.UNIVERSAL``
    Maximum compatibility: tries every anchor in a sensible order.
"""

class Waterfall:
    """Ordered sequence of ``PathMode`` steps for fallback path resolution."""

    def __init__(self, *steps: PathMode) -> None:
        self._steps: tuple[PathMode, ...] = steps

    # ------------------------------------------------------------------ #
    #  Pre-built strategies (assigned after class definition)              #
    # ------------------------------------------------------------------ #

    #: Read-optimized for deployed exes.
    #: ``EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE``
    EXE_PREFER_BUNDLED: "Waterfall"

    #: Standard development fallback chain.
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
