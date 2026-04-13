"""
Lifecycle / versioning decorators — mark functions as deprecated, experimental,
or scheduled for removal; document API evolution.

Migrated from decorators_pack.py:
  - deprecated
  - battered
"""

import functools
import warnings


def deprecated(reason: str = ""):
    """
    Mark a function as deprecated.
    Issues a ``DeprecationWarning`` on every call.

    :param reason: Explanation or replacement suggestion.

    e.g.::

        @deprecated("Use `new_func` instead.")
        def old_func(x):
            return x + 1
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"Function {func.__name__!r} is deprecated."
            if reason:
                msg += f" {reason}"
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def battered(reason: str = ""):
    """
    Mark a function as fragile or unreliable.
    Issues a ``UserWarning`` on every call.

    :param reason: Explanation of known fragility.

    e.g.::

        @battered("Fails with empty inputs.")
        def risky_func(x):
            return 10 / x
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"Function {func.__name__!r} is battered and may break."
            if reason:
                msg += f" {reason}"
            warnings.warn(msg, category=UserWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def experimental(reason: str = ""):
    """
    Mark a function as experimental (API may change without prior notice).
    Issues a ``FutureWarning`` on the *first* call only.

    :param reason: Optional context or stability notes.

    e.g.::

        @experimental("Behaviour may change in v2.")
        def new_feature():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not wrapper._warned:
                msg = f"Function {func.__name__!r} is experimental and may change without notice."
                if reason:
                    msg += f" {reason}"
                warnings.warn(msg, category=FutureWarning, stacklevel=2)
                wrapper._warned = True
            return func(*args, **kwargs)

        wrapper._warned = False
        return wrapper

    return decorator


def removed_in(version: str, reason: str = ""):
    """
    Warn that the function is scheduled to be removed in *version*.
    Issues a ``DeprecationWarning`` on every call.

    :param version: Target version string, e.g. ``"2.0.0"``.
    :param reason:  Migration hint.

    e.g.::

        @removed_in("2.0.0", reason="Use `new_api()` instead.")
        def legacy_api():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"Function {func.__name__!r} will be removed in version {version}."
            if reason:
                msg += f" {reason}"
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def since(version: str):
    """
    Attach version metadata to a function (no runtime side effects).
    Accessible via ``func.since_version``.

    :param version: Version string when the function was introduced.

    e.g.::

        @since("1.3.0")
        def new_feature():
            ...

        print(new_feature.since_version)   # "1.3.0"
    """

    def decorator(func):
        func.since_version = version

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.since_version = version
        return wrapper

    return decorator
