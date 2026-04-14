"""
Value assertions — validate numeric ranges, emptiness, membership, and patterns.
"""

import re as _re


def assert__is_positive(obj):
    """Assert that *obj* is a positive number (> 0)."""
    if not isinstance(obj, (int, float)) or isinstance(obj, bool) or obj <= 0:
        raise ValueError(f"❌ param must be a positive number, got {obj!r}")
    return True


def assert__is_non_negative(obj):
    """Assert that *obj* is a non-negative number (>= 0)."""
    if not isinstance(obj, (int, float)) or isinstance(obj, bool) or obj < 0:
        raise ValueError(f"❌ param must be a non-negative number, got {obj!r}")
    return True


def assert__is_not_empty(obj):
    """Assert that *obj* is not ``None`` and not empty (works for str, list, dict, set, …)."""
    if obj is None:
        raise ValueError("❌ param must not be None")
    if hasattr(obj, "__len__") and len(obj) == 0:
        raise ValueError(f"❌ param must not be empty (type: {type(obj).__name__})")
    return True


def assert__in_range(obj, low, high, *, inclusive=True):
    """Assert that *obj* is within [*low*, *high*] (inclusive) or (*low*, *high*) (exclusive)."""
    if not isinstance(obj, (int, float)) or isinstance(obj, bool):
        raise TypeError(f"❌ param must be a number, got {type(obj).__name__}")
    if inclusive:
        if not (low <= obj <= high):
            raise ValueError(f"❌ param must be in range [{low}, {high}], got {obj}")
    else:
        if not (low < obj < high):
            raise ValueError(f"❌ param must be in range ({low}, {high}), got {obj}")
    return True


def assert__is_one_of(obj, options):
    """Assert that *obj* is a member of *options* (any iterable)."""
    if obj not in options:
        raise ValueError(f"❌ param must be one of {list(options)!r}, got {obj!r}")
    return True


def assert__matches_pattern(obj, pattern: str):
    """Assert that the string *obj* fully matches the given regex *pattern*."""
    if not isinstance(obj, str):
        raise TypeError(f"❌ param must be of type str for pattern matching, got {type(obj).__name__}")
    if not _re.fullmatch(pattern, obj):
        raise ValueError(f"❌ param does not match pattern '{pattern}', got {obj!r}")
    return True
