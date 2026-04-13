import time
import functools
import warnings

def function_timer(func):
    """計時用 decorator，印出函數執行時間，不影響原有邏輯與回傳值"""
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
    A decorator that:
        - Measures execution time
        - Automatically returns (result, time) if `with_time_return=True`
        - Keeps the function signature compatible with @abstractmethod
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

def deprecated(reason: str = ""):
    """
    Decorator to mark functions as deprecated.
    It will issue a warning when the function is called.

    :param reason: Optional explanation or replacement suggestion.

    e.g.:
        @deprecated("Use `new_function` instead.")
        def old_function(x):
            return x + 1
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warn_msg = f"Function {func.__name__} is deprecated."
            if reason:
                warn_msg += f" Reason: {reason}"
            warnings.warn(warn_msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator

def battered(reason: str = ""):
    """
    Similar to @deprecated but emphasizes that the function is unreliable or fragile.

    :param reason: Optional explanation.

    e.g.:
        @battered("This function often fails with edge cases.")
        def fragile_function(x):
            return 10 / x
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warn_msg = f"Function {func.__name__} is battered and may break."
            if reason:
                warn_msg += f" Reason: {reason}"
            warnings.warn(warn_msg, category=UserWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    return decorator
