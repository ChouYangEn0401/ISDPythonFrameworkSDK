"""
Concurrency decorators — run_in_thread, synchronized.
"""

import functools
import threading


def run_in_thread(func):
    """
    Run the decorated function in a separate daemon thread.
    Returns the ``threading.Thread`` object; call ``.join()`` to wait for completion.

    e.g.::

        @run_in_thread
        def background_task():
            time.sleep(5)
            print("done")

        t = background_task()   # starts immediately, returns Thread
        t.join()                # blocks until finished
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    return wrapper


def synchronized(lock=None):
    """
    Serialize access to the decorated function using a threading lock.
    Supports ``@synchronized`` (auto-creates a lock) and ``@synchronized(my_lock)``.

    :param lock: An optional ``threading.Lock`` or ``threading.RLock`` instance.

    e.g.::

        @synchronized
        def critical_section():
            ...

        shared_lock = threading.Lock()

        @synchronized(shared_lock)
        def another_critical():
            ...
    """
    # @synchronized  (no parentheses — lock is actually the function)
    if callable(lock):
        fn = lock
        fn_lock = threading.Lock()

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with fn_lock:
                return fn(*args, **kwargs)

        return wrapper

    # @synchronized() or @synchronized(my_lock)
    def decorator(func):
        fn_lock = lock or threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with fn_lock:
                return func(*args, **kwargs)

        return wrapper

    return decorator
