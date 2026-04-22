"""
_meta.py — SingletonABCMeta

Combines ``ABCMeta`` (needed for abstract base classes) with the
singleton-enforcement logic from the framework's ``SingletonMetaclass``.

Used exclusively by ``SingletonPathManager`` so that it can both:
  1. Inherit from ``IPathManager`` (an ABC), and
  2. Behave as a singleton (only one instance per class).

All changes remain within ``path_manager/`` — the root ``base/Singleton.py``
is intentionally left unmodified.
"""

from __future__ import annotations

from abc import ABCMeta
from typing import Any, Dict, Type


class SingletonABCMeta(ABCMeta):
    """
    ``ABCMeta`` subclass that additionally enforces singleton instantiation.

    When a class using this metaclass is instantiated for the first time,
    a real instance is created and stored.  All subsequent calls return
    the same instance without re-calling ``__init__``.

    If the class defines ``_initialize_manager(self)``, that method is
    called exactly once immediately after first creation.
    """

    _instances: Dict[Type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            if hasattr(instance, "_initialize_manager"):
                instance._initialize_manager()
            cls._instances[cls] = instance
        return cls._instances[cls]
