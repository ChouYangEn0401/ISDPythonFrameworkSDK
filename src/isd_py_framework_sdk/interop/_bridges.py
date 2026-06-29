"""Inter-module bridges — the inward-facing twin of :mod:`_optional`.

Where :mod:`isd_py_framework_sdk._optional` governs **third-party** dependencies
(*is ``cryptography`` / ``openpyxl`` installed?*), this module governs
**sibling sub-package** dependencies: the handful of places where one feature
sub-package legitimately needs to call into another (e.g. ``credential_vault``
unsealing a ``CK1`` token via ``cipher_kit``).

Why a dedicated layer?
----------------------
The sub-packages are intentionally decoupled, but a few real cross-calls exist.
Left scattered, they rot: someone adds a coupling, forgets which extra it needs,
and a partial install (``pip install isd-py-framework-sdk[credential_vault]``
*without* ``[cipher_kit]``) breaks with a cryptic ``ModuleNotFoundError`` deep
in a backend instead of the project's standard, actionable message.

``interop`` centralises every such bridge behind :func:`require_feature`, so:

* there is a single, documented registry of who-uses-whom (see ``agent.md``);
* every bridge fails with the *same* :class:`MissingOptionalDependencyError`
  voice as the rest of the SDK, naming the exact ``pip install ...[extra]``;
* merely *importing* a sub-package never trips a bridge — the heavy backend is
  only demanded when the cross-call is actually executed.

The key subtlety
----------------
``import isd_py_framework_sdk.cipher_kit`` **always succeeds**: sibling
sub-packages ship in the same wheel and load lazily.  What can be missing is the
sub-package's heavy *third-party* backend (``cryptography`` for ``cipher_kit``,
``openpyxl`` for ``excel_painter``).  So :func:`require_feature` does not merely
import the sibling — it first verifies that representative backend through
:func:`_optional.require`, raising the standard error if the backend is absent,
and only then imports and returns the sub-package module.
"""
from __future__ import annotations

import importlib
from types import ModuleType

from .._optional import MissingOptionalDependencyError, have, require

__all__ = [
    "FEATURE_EXTRAS",
    "FEATURE_PROBES",
    "require_feature",
    "has_feature",
    "MissingOptionalDependencyError",
]

# feature name → the extras group that makes it fully usable.
# (message_logger is core/zero-heavy-dep on its type-only bridge, so it is not
#  listed here — see ``agent.md``.)
FEATURE_EXTRAS: dict[str, str] = {
    "cipher_kit": "cipher_kit",        # needs cryptography
    "excel_painter": "excel_painter",  # needs openpyxl (+ wcwidth)
}

# feature name → the representative heavy backend whose presence we probe.
# Sibling sub-packages always import; only their third-party backend can be
# missing, so this is what tells "installed" from "not installed" apart.
FEATURE_PROBES: dict[str, str] = {
    "cipher_kit": "cryptography",
    "excel_painter": "openpyxl",
}

# feature name → the importable module path of the sibling sub-package.
_FEATURE_MODULES: dict[str, str] = {
    "cipher_kit": "isd_py_framework_sdk.cipher_kit",
    "excel_painter": "isd_py_framework_sdk.excel_painter",
}


def _check_known(name: str) -> None:
    if name not in FEATURE_EXTRAS:
        raise KeyError(
            f"Unknown interop feature {name!r}. "
            f"Known features: {sorted(FEATURE_EXTRAS)}."
        )


def require_feature(name: str) -> ModuleType:
    """Return sibling sub-package *name*, or raise the SDK's standard error.

    The sub-package itself always imports (it ships in the same wheel); what may
    be missing is its heavy third-party backend.  This first verifies that
    backend via :func:`_optional.require` — so a missing backend yields the
    familiar :class:`MissingOptionalDependencyError` naming
    ``pip install isd-py-framework-sdk[<extra>]`` — then imports and returns the
    sub-package module.

    :param name: a key of :data:`FEATURE_EXTRAS` (e.g. ``"cipher_kit"``).
    :raises KeyError: if *name* is not a registered feature.
    :raises MissingOptionalDependencyError: if the feature's backend is absent.
    """
    _check_known(name)
    # Verify the heavy backend with the standard voice/behaviour.
    require(FEATURE_PROBES[name], extra=FEATURE_EXTRAS[name], feature=name)
    return importlib.import_module(_FEATURE_MODULES[name])


def has_feature(name: str) -> bool:
    """Return ``True`` if feature *name*'s heavy backend is importable.

    A non-raising capability probe (mirrors :func:`_optional.have`); use it to
    branch on availability without forcing the dependency.
    """
    _check_known(name)
    return have(FEATURE_PROBES[name])
