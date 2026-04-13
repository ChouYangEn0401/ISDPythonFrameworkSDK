"""
GUI decorators — thread-safety guards, debouncing, and widget state helpers.

All helpers are UI-toolkit-agnostic unless noted.
"""

import functools
import threading
import time


def require_main_thread(func):
    """
    Assert that the decorated function is called from the main thread.
    Raises ``RuntimeError`` if invoked from a background thread.

    Use this to protect Tkinter / Qt widget operations.

    e.g.::

        @require_main_thread
        def update_label(text):
            label.config(text=text)
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError(
                f"[GUI] '{func.__name__}' must be called from the main thread, "
                f"but was called from '{threading.current_thread().name}'."
            )
        return func(*args, **kwargs)

    return wrapper


def debounce(wait: float):
    """
    Delay the decorated function until *wait* seconds have elapsed since the last call.
    Intermediate calls reset the timer — only the final call executes.

    Useful for responding to rapid user input (search boxes, resize events, …).

    :param wait: Quiet period in seconds after the last call before execution.

    e.g.::

        @debounce(0.3)
        def on_search_change(text):
            ...
    """

    def decorator(func):
        timer: list = [None]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def _fire():
                timer[0] = None
                func(*args, **kwargs)

            if timer[0] is not None:
                timer[0].cancel()
            t = threading.Timer(wait, _fire)
            t.daemon = True
            timer[0] = t
            t.start()

        return wrapper

    return decorator


def gui_error_handler(on_error=None):
    """
    Catch any exception raised during a GUI event handler and call *on_error*
    with the exception instead of crashing the UI loop.

    :param on_error: ``Callable[[Exception], None]``. Defaults to ``print``.

    e.g.::

        @gui_error_handler(on_error=lambda e: status_bar.set(str(e)))
        def on_button_click():
            risky_operation()
    """
    _handler = on_error if callable(on_error) else print

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                _handler(exc)
                return None

        return wrapper

    return decorator


def disable_widget_during_run(get_widget):
    """
    Disable a widget before calling the function and re-enable it afterwards.
    Useful for preventing double-clicks on buttons.

    :param get_widget: ``Callable[[], widget]`` — returns the widget at call time
                       (lazy evaluation so the widget can be created after decoration).

    e.g.::

        @disable_widget_during_run(lambda: run_button)
        def on_run_clicked():
            do_long_work()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            widget = get_widget()
            try:
                widget.config(state="disabled")
            except Exception:
                pass
            try:
                return func(*args, **kwargs)
            finally:
                try:
                    widget.config(state="normal")
                except Exception:
                    pass

        return wrapper

    return decorator


def run_after(delay_ms: int, get_scheduler):
    """
    Schedule the function to run after *delay_ms* milliseconds using the
    scheduler returned by *get_scheduler* (e.g. ``tk.Tk.after``).

    :param delay_ms:     Delay in milliseconds.
    :param get_scheduler: ``Callable[[], after_fn]`` — returns the ``after``
                          callable of the current event-loop owner.

    e.g.::

        @run_after(200, lambda: root.after)
        def refresh_view():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            after = get_scheduler()
            after(delay_ms, lambda: func(*args, **kwargs))

        return wrapper

    return decorator
