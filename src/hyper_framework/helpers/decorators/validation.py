"""
Validation decorators — guard function inputs and outputs at the boundary.
Implements SRP: each decorator has exactly ONE validation concern.
"""

import functools


def not_none(*arg_names: str):
    """
    Assert that the named keyword arguments (or positional args by index if names
    match the function signature) are not ``None`` before the function executes.

    :param arg_names: Names of parameters that must not be ``None``.

    e.g.::

        @not_none("user_id", "payload")
        def create_record(user_id, payload):
            ...
    """

    def decorator(func):
        import inspect

        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name in arg_names:
                if name in bound.arguments and bound.arguments[name] is None:
                    raise ValueError(
                        f"[{func.__name__}] Argument '{name}' must not be None."
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_args(**validators):
    """
    Validate specific keyword arguments before calling the function.
    Each validator is a ``Callable[[value], bool]``; raises ``ValueError`` on failure.

    :param validators: Mapping of ``arg_name → predicate``.

    e.g.::

        @validate_args(
            age=lambda v: isinstance(v, int) and v >= 0,
            name=lambda v: isinstance(v, str) and len(v) > 0,
        )
        def register_user(name, age):
            ...
    """

    def decorator(func):
        import inspect

        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, predicate in validators.items():
                if name in bound.arguments:
                    value = bound.arguments[name]
                    if not predicate(value):
                        raise ValueError(
                            f"[{func.__name__}] Argument '{name}' failed validation "
                            f"(got {value!r})."
                        )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_return(validator, message: str = ""):
    """
    Validate the return value after the function executes.
    Raises ``ValueError`` if the validator returns ``False``.

    :param validator: ``Callable[[return_value], bool]``.
    :param message:   Custom error message fragment.

    e.g.::

        @validate_return(lambda v: isinstance(v, list) and len(v) > 0,
                         message="must be a non-empty list")
        def fetch_items():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not validator(result):
                msg = f"[{func.__name__}] Return value failed validation"
                if message:
                    msg += f": {message}"
                msg += f" (got {result!r})."
                raise ValueError(msg)
            return result

        return wrapper

    return decorator


def ensure_type(**type_map):
    """
    Assert that specified arguments are instances of the mapped types.
    Raises ``TypeError`` on mismatch.

    :param type_map: Mapping of ``arg_name → type_or_tuple_of_types``.

    e.g.::

        @ensure_type(user_id=int, tags=list)
        def tag_user(user_id, tags):
            ...
    """

    def decorator(func):
        import inspect

        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, expected_type in type_map.items():
                if name in bound.arguments:
                    value = bound.arguments[name]
                    if not isinstance(value, expected_type):
                        exp_name = (
                            expected_type.__name__
                            if isinstance(expected_type, type)
                            else str(expected_type)
                        )
                        raise TypeError(
                            f"[{func.__name__}] Argument '{name}' must be "
                            f"{exp_name}, got {type(value).__name__}."
                        )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def clamp_return(min_val, max_val):
    """
    Clamp a numeric return value to ``[min_val, max_val]`` silently.

    e.g.::

        @clamp_return(0.0, 1.0)
        def compute_probability():
            return some_raw_score()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return max(min_val, min(max_val, result))

        return wrapper

    return decorator


def non_empty_return(message: str = ""):
    """
    Assert that the return value is not ``None`` and not empty.
    Raises ``ValueError`` otherwise.

    e.g.::

        @non_empty_return("Expected at least one row")
        def query_db():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            is_empty = result is None or (hasattr(result, "__len__") and len(result) == 0)
            if is_empty:
                msg = f"[{func.__name__}] Returned empty or None."
                if message:
                    msg += f" {message}"
                raise ValueError(msg)
            return result

        return wrapper

    return decorator
