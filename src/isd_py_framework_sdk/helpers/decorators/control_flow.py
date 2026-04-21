"""
Control-flow decorators — retry, once, suppress, throttle, timeout.
"""

import functools
import time
import threading


def retry(max_attempts: int = 3, delay: float = 0.0, backoff: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Retry a function on failure.

    :param max_attempts: Maximum number of attempts (default: 3).
    :param delay: Initial delay between retries in seconds (default: 0).
    :param backoff: Multiplier applied to delay after each retry (default: 1.0).
    :param exceptions: Tuple of exception types to catch (default: ``(Exception,)``).

    e.g.::

        @retry(max_attempts=5, delay=1.0, backoff=2.0, exceptions=(IOError,))
        def fetch_data():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        if current_delay > 0:
                            time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


def once(func):
    """
    Ensure a function is only executed once.
    Subsequent calls return the cached result from the first invocation.

    e.g.::

        @once
        def load_config():
            print("loading…")
            return {"key": "value"}

        load_config()  # prints "loading…", returns dict
        load_config()  # returns cached dict, no print
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not wrapper._called:
            wrapper._result = func(*args, **kwargs)
            wrapper._called = True
        return wrapper._result

    wrapper._called = False
    wrapper._result = None
    return wrapper


def suppress_exceptions(*exceptions, default=None, log: bool = False):
    """
    Catch specified exceptions and return *default* instead of propagating.

    :param exceptions: Exception types to catch (default: ``Exception``).
    :param default: Value to return on exception (default: ``None``).
    :param log: If ``True``, print the exception to stdout (default: ``False``).

    e.g.::

        @suppress_exceptions(ZeroDivisionError, default=-1)
        def safe_divide(a, b):
            return a / b
    """
    if not exceptions:
        exceptions = (Exception,)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log:
                    print(f"[suppress_exceptions] {func.__name__}: {type(e).__name__}: {e}")
                return default

        return wrapper

    return decorator


def throttle(interval: float):
    """
    Limit function execution to at most once per *interval* seconds.
    Calls within the throttle window are silently skipped (return ``None``).

    :param interval: Minimum seconds between invocations.

    e.g.::

        @throttle(2.0)
        def send_heartbeat():
            ...
    """

    def decorator(func):
        last_call = [0.0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_call[0] >= interval:
                last_call[0] = now
                return func(*args, **kwargs)
            return None

        return wrapper

    return decorator


def timeout(seconds: float):
    """
    Abort function execution if it exceeds *seconds*.
    Uses threading internally; the decorated function runs in a daemon thread.

    Raises ``TimeoutError`` if the function does not complete in time.

    .. note::

        Cannot forcefully kill CPU-bound code — relies on the thread finishing
        naturally or the function being IO-bound.

    :param seconds: Maximum execution time in seconds.

    e.g.::

        @timeout(5.0)
        def slow_network_call():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result: list = [None]
            exception: list = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                raise TimeoutError(
                    f"Function '{func.__name__}' timed out after {seconds:.1f}s"
                )

            if exception[0] is not None:
                raise exception[0]
            return result[0]

        return wrapper

    return decorator
