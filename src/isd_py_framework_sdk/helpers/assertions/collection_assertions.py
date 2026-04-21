"""
Collection assertions — validate length, keys, uniqueness, and contents of collections.
"""

from __future__ import annotations
from typing import Any, Iterable


def assert__has_length(obj, expected_length: int):
    """Assert that ``len(obj)`` equals *expected_length*."""
    if not hasattr(obj, "__len__"):
        raise TypeError(f"❌ param of type {type(obj).__name__} does not support len()")
    if len(obj) != expected_length:
        raise ValueError(f"❌ param must have length {expected_length}, got {len(obj)}")
    return True


def assert__min_length(obj, min_len: int):
    """Assert that ``len(obj) >= min_len``."""
    if not hasattr(obj, "__len__"):
        raise TypeError(f"❌ param of type {type(obj).__name__} does not support len()")
    if len(obj) < min_len:
        raise ValueError(f"❌ param must have at least {min_len} items, got {len(obj)}")
    return True


def assert__max_length(obj, max_len: int):
    """Assert that ``len(obj) <= max_len``."""
    if not hasattr(obj, "__len__"):
        raise TypeError(f"❌ param of type {type(obj).__name__} does not support len()")
    if len(obj) > max_len:
        raise ValueError(f"❌ param must have at most {max_len} items, got {len(obj)}")
    return True


def assert__all_keys_exist(d: dict, keys: Iterable[Any]):
    """Assert that all *keys* exist in dict *d*."""
    if not isinstance(d, dict):
        raise TypeError(f"❌ first param must be of type dict, got {type(d).__name__}")
    missing = [k for k in keys if k not in d]
    if missing:
        raise KeyError(f"❌ missing keys: {missing}")
    return True


def assert__is_unique(obj):
    """Assert that all elements in *obj* are unique (requires hashable elements)."""
    if not hasattr(obj, "__iter__"):
        raise TypeError(f"❌ param of type {type(obj).__name__} must be iterable")
    items = list(obj)
    if len(items) != len(set(items)):
        raise ValueError("❌ param contains duplicate elements")
    return True


def assert__no_none_values(obj):
    """Assert that *obj* (dict or iterable) contains no ``None`` values."""
    if isinstance(obj, dict):
        none_keys = [k for k, v in obj.items() if v is None]
        if none_keys:
            raise ValueError(f"❌ dict contains None values for keys: {none_keys}")
    elif hasattr(obj, "__iter__"):
        if any(x is None for x in obj):
            raise ValueError("❌ collection must not contain None values")
    else:
        raise TypeError(f"❌ param of type {type(obj).__name__} must be iterable")
    return True


def assert__contains_in_list(lst, item):
    """Assert that *item* is present in *lst* (list)."""
    if not isinstance(lst, list):
        raise TypeError(f"❌ first param must be of type list, got {type(lst).__name__}")
    if item not in lst:
        raise ValueError(f"❌ list does not contain {item!r}")
    return True


def assert__contains_in_str(s: str, substring: str):
    """Assert that *substring* is contained within string *s*."""
    if not isinstance(s, str):
        raise TypeError(f"❌ first param must be of type str, got {type(s).__name__}")
    if not isinstance(substring, str):
        raise TypeError(f"❌ substring must be of type str, got {type(substring).__name__}")
    if substring not in s:
        raise ValueError(f"❌ string does not contain {substring!r}")
    return True


def assert__contains_in_dataclass(obj, field_name: str):
    """Assert that dataclass *obj* has a field named *field_name*."""
    try:
        from dataclasses import is_dataclass
    except Exception:
        is_dataclass = lambda x: False

    if not is_dataclass(obj):
        raise TypeError(f"❌ first param must be a dataclass instance, got {type(obj).__name__}")
    if not isinstance(field_name, str):
        raise TypeError("❌ field_name must be of type str")
    if not hasattr(obj, field_name):
        raise AttributeError(f"❌ dataclass does not have field '{field_name}'")
    return True


def assert__contains_in_object(obj, attr_name: str):
    """Assert that object *obj* has attribute named *attr_name*."""
    if not hasattr(obj, '__dict__') and not hasattr(obj, attr_name):
        raise TypeError(f"❌ first param must be an object with attributes, got {type(obj).__name__}")
    if not isinstance(attr_name, str):
        raise TypeError("❌ attr_name must be of type str")
    if not hasattr(obj, attr_name):
        raise AttributeError(f"❌ object does not have attribute '{attr_name}'")
    return True
