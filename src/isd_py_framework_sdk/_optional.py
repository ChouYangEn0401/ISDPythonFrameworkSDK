"""
Optional-dependency plumbing — keeps the "core install = zero heavy deps"
promise.

Heavy third-party backends (``pandas``, ``openpyxl``, ``colorama``,
``cryptography`` …) are **never** imported at ``import isd_py_framework_sdk``
time.  A feature pulls its backend in lazily through :func:`require`, and if the
backend is missing the user gets one clear, consistent message naming the exact
extra to install (mirrors pandas' *"Missing optional dependency …"*).

When a feature silently substitutes one backend for another (e.g. ``argon2id``
→ ``scrypt``), use :func:`notify_substitution` to emit a single,
numpy/pandas-style heads-up instead of failing.
"""
from __future__ import annotations

import importlib
import warnings
from types import ModuleType

__all__ = [
    "MissingOptionalDependencyError",
    "DependencySubstitutionWarning",
    "require",
    "have",
    "notify_substitution",
]

# pip distribution name (what goes inside ``pip install <dist>[extra]``).
_DIST = "isd-py-framework-sdk"


class MissingOptionalDependencyError(ImportError):
    """A feature needs an optional backend that is not installed.

    Subclasses :class:`ImportError` on purpose, so any existing
    ``except ImportError`` handler keeps catching it (API-preserving).
    """


class DependencySubstitutionWarning(UserWarning):
    """Emitted once when a feature falls back to an alternative backend."""


def require(module: str, *, extra: str, feature: str | None = None) -> ModuleType:
    """Import *module* lazily, or raise a helpful, actionable error.

    :param module:  top-level import name, e.g. ``"openpyxl"``.
    :param extra:   the extras group that provides it, e.g. ``"unified_io-excel"``.
    :param feature: optional human description of what needs it.
    :returns:       the imported module.
    :raises MissingOptionalDependencyError: if *module* cannot be imported.
    """
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        for_feature = f" for {feature}" if feature else ""
        raise MissingOptionalDependencyError(
            f"Missing optional dependency {module!r}{for_feature}. "
            f"Install it with:  pip install {_DIST}[{extra}]"
        ) from exc


def have(module: str) -> bool:
    """Return ``True`` if *module* can be imported (capability probe)."""
    try:
        importlib.import_module(module)
        return True
    except ImportError:
        return False


# Messages already warned about, so hot paths do not spam the user.
_seen: set[str] = set()


def notify_substitution(message: str, *, once: bool = True) -> None:
    """Emit a numpy/pandas-style notice that a backend was substituted.

    With ``once=True`` (default) the same message warns only a single time per
    process.

    :param message: human-readable explanation of what was swapped and why.
    :param once:    de-duplicate identical messages within the process.
    """
    if once:
        if message in _seen:
            return
        _seen.add(message)
    warnings.warn(message, category=DependencySubstitutionWarning, stacklevel=2)
