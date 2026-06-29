"""
isd_py_framework_sdk.interop
============================
Centralised, documented bridges between sibling sub-packages.

The SDK's sub-packages are deliberately decoupled, but a few real cross-calls
exist (``credential_vault`` → ``cipher_kit``, ``unified_io`` → ``excel_painter``,
``monitoring`` → ``message_logger`` for types only).  Every such bridge is routed
through :func:`require_feature` so that a *partial install* fails with the SDK's
standard, actionable message instead of a cryptic backend error.

Think of it as the inward-facing twin of :mod:`isd_py_framework_sdk._optional`:

* ``_optional`` answers *"is this third-party package installed?"*;
* ``interop``  answers *"which sibling sub-package does this feature need, and
  what extra unlocks it?"* — built on top of ``_optional``, not reinventing it.

See ``agent.md`` for the authoritative registry of every cross-module bridge and
the rule that any new cross-call must go through :func:`require_feature`.

This layer is intentionally **not** part of the top-level flat public API.
Advanced callers may import it directly::

    from isd_py_framework_sdk.interop import require_feature, has_feature
"""
from __future__ import annotations

from .._optional import MissingOptionalDependencyError
from ._bridges import (
    FEATURE_EXTRAS,
    FEATURE_PROBES,
    has_feature,
    require_feature,
)

__all__ = [
    "require_feature",
    "has_feature",
    "FEATURE_EXTRAS",
    "FEATURE_PROBES",
    # re-exported for convenience: this is what require_feature raises.
    "MissingOptionalDependencyError",
]
