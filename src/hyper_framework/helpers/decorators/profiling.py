"""
Profiling decorators — timing, call counting, and memory measurement.

Migrated from decorators_pack.py:
  - function_timer
  - timed_and_conditional_return
"""

import functools
import time
import tracemalloc


def function_timer(func):
    """
    Print the wall-clock execution time of the decorated function.
    Does not alter the return value.

    e.g.::

        @function_timer
        def slow_task():
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"--- 開始執行：{func.__name__} ---")
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"--- 結束執行：{func.__name__}，耗時 {elapsed:.2f} 秒 ---")
        return result

    return wrapper


def timed_and_conditional_return(func):
    """
    Measure execution time and optionally return ``(result, elapsed_seconds)``
    by passing ``with_time_return=True`` at call time.

    e.g.::

        @timed_and_conditional_return
        def measured_task():
            return "result"

        result = measured_task()
        result, elapsed = measured_task(with_time_return=True)
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with_time_return = kwargs.get("with_time_return", False)

        print(f"--- 開始執行：{func.__name__} ---")
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"--- 結束執行：{func.__name__}，耗時 {elapsed:.2f} 秒 ---")

        if with_time_return:
            return result, elapsed
        return result

    return wrapper


def log_call(*, show_args: bool = False, show_return: bool = False):
    """
    Log each call to the decorated function (name, optional args, optional return value).

    :param show_args:   Print positional/keyword arguments (default: ``False``).
    :param show_return: Print the return value (default: ``False``).

    e.g.::

        @log_call(show_args=True, show_return=True)
        def add(a, b):
            return a + b
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if show_args:
                print(f"[CALL] {func.__name__}  args={args!r}  kwargs={kwargs!r}")
            else:
                print(f"[CALL] {func.__name__}()")
            result = func(*args, **kwargs)
            if show_return:
                print(f"[RETURN] {func.__name__} → {result!r}")
            return result

        return wrapper

    return decorator


def count_calls(func):
    """
    Track how many times the decorated function has been invoked.
    Access the counter via ``func.call_count``.

    e.g.::

        @count_calls
        def process():
            ...

        process(); process()
        print(process.call_count)  # 2
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.call_count += 1
        return func(*args, **kwargs)

    wrapper.call_count = 0
    return wrapper


def profile_memory(func):
    """
    Measure peak memory allocated during function execution using ``tracemalloc``.
    Prints the peak allocation in KiB after the function returns.

    e.g.::

        @profile_memory
        def build_large_matrix():
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        result = func(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"[MEMORY] {func.__name__}  peak={peak / 1024:.1f} KiB")
        return result

    return wrapper
