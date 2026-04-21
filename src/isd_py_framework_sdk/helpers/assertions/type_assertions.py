"""
Type assertions — validate that values are of expected Python types.
"""


def assert__is_int(obj):
    """Assert that *obj* is strictly ``int`` (``bool`` is excluded)."""
    if not isinstance(obj, int) or isinstance(obj, bool):
        raise TypeError(f"❌ param must be of type int, got {type(obj).__name__}")
    return True


def assert__is_float(obj):
    """Assert that *obj* is strictly ``float``."""
    if not isinstance(obj, float):
        raise TypeError(f"❌ param must be of type float, got {type(obj).__name__}")
    return True


def assert__is_number(obj):
    """Assert that *obj* is ``int`` or ``float`` (``bool`` is excluded)."""
    if not isinstance(obj, (int, float)) or isinstance(obj, bool):
        raise TypeError(f"❌ param must be a number (int | float), got {type(obj).__name__}")
    return True


def assert__is_bool(obj):
    """Assert that *obj* is strictly ``bool``."""
    if not isinstance(obj, bool):
        raise TypeError(f"❌ param must be of type bool, got {type(obj).__name__}")
    return True


def assert__is_dict(obj):
    """Assert that *obj* is a ``dict``."""
    if not isinstance(obj, dict):
        raise TypeError(f"❌ param must be of type dict, got {type(obj).__name__}")
    return True


def assert__is_list(obj):
    """Assert that *obj* is a ``list``."""
    if not isinstance(obj, list):
        raise TypeError(f"❌ param must be of type list, got {type(obj).__name__}")
    return True


def assert__is_tuple(obj):
    """Assert that *obj* is a ``tuple``."""
    if not isinstance(obj, tuple):
        raise TypeError(f"❌ param must be of type tuple, got {type(obj).__name__}")
    return True


def assert__is_set(obj):
    """Assert that *obj* is a ``set``."""
    if not isinstance(obj, set):
        raise TypeError(f"❌ param must be of type set, got {type(obj).__name__}")
    return True


def assert__is_callable(obj):
    """Assert that *obj* is callable."""
    if not callable(obj):
        raise TypeError(f"❌ param must be callable, got {type(obj).__name__}")
    return True


def assert__is_none(obj):
    """Assert that *obj* is ``None``."""
    if obj is not None:
        raise TypeError(f"❌ param must be None, got {type(obj).__name__}")
    return True


def assert__is_not_none(obj):
    """Assert that *obj* is not ``None``."""
    if obj is None:
        raise TypeError("❌ param must not be None")
    return True


def assert__is_instance(obj, cls):
    """Assert that *obj* is an instance of *cls* (or tuple of classes)."""
    if not isinstance(obj, cls):
        expected = cls.__name__ if isinstance(cls, type) else str(cls)
        raise TypeError(f"❌ param must be an instance of {expected}, got {type(obj).__name__}")
    return True


def assert__is_subclass(cls, parent):
    """Assert that *cls* is a subclass of *parent*."""
    if not (isinstance(cls, type) and issubclass(cls, parent)):
        raise TypeError(f"❌ {cls!r} must be a subclass of {parent.__name__}")
    return True


def assert__is_list_of_int(obj):
    """Assert that *obj* is ``list[int]`` (no booleans)."""
    if not (isinstance(obj, list) and all(isinstance(x, int) and not isinstance(x, bool) for x in obj)):
        raise TypeError("❌ param must be of type list[int]")
    return True


def assert__is_list_of_float(obj):
    """Assert that *obj* is ``list[float]``."""
    if not (isinstance(obj, list) and all(isinstance(x, float) for x in obj)):
        raise TypeError("❌ param must be of type list[float]")
    return True


def assert__is_list_of_number(obj):
    """Assert that *obj* is ``list[int | float]`` (no booleans)."""
    if not (isinstance(obj, list) and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in obj)):
        raise TypeError("❌ param must be of type list[int | float]")
    return True


def assert__is_dict_of_str_to_str(obj):
    """Assert that *obj* is ``dict[str, str]``."""
    if not (isinstance(obj, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in obj.items())):
        raise TypeError("❌ param must be of type dict[str, str]")
    return True


def assert__is_str(obj):
    if not isinstance(obj, str):
        raise TypeError("❌ param must be of type str")
    return True


def assert__is_list_of_str(obj):
    if not (isinstance(obj, list) and all(isinstance(s, str) for s in obj)):
        raise TypeError("❌ param must be of type list[str]")
    return True


def assert__is_list_of_list_of_str(obj):
    if not (isinstance(obj, list) and all(isinstance(sub, list) and all(isinstance(s, str) for s in sub) for sub in obj)):
        raise TypeError("❌ param must be of type list[list[str]]")
    return True


def assert__is_list_of_tuple_of_str(obj):
    if not (isinstance(obj, list) and all(isinstance(sub, tuple) and all(isinstance(s, str) for s in sub) for sub in obj)):
        raise TypeError("❌ param must be of type list[tuple[str]]")
    return True
