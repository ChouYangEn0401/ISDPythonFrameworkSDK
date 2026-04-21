"""
Monitoring / observability decorators — emit metrics, ping watchdogs,
run health checks, and alert on failure.
"""

import functools
import time


def emit_metric(name: str = "", unit: str = "s"):
    """
    Measure wall-clock time and emit a metric after the function returns.
    Out of the box the metric is printed; swap *backend* for real telemetry.

    :param name:    Metric name (defaults to ``"<func_name>.duration"``).
    :param unit:    Unit label for the printout (default: ``"s"``).

    e.g.::

        @emit_metric("api.fetch_users")
        def fetch_users():
            ...
    """

    def decorator(func):
        metric_name = name or f"{func.__name__}.duration"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - t0
            print(f"[METRIC] {metric_name}={elapsed:.4f}{unit}")
            return result

        return wrapper

    return decorator


def watchdog_ping(registry: dict, key: str = ""):
    """
    Update a watchdog registry with the current timestamp on every call.
    An external supervisor can check ``registry[key]`` to confirm liveness.

    :param registry: A shared ``dict`` where the timestamp is stored.
    :param key:      Registry key (defaults to the function name).

    e.g.::

        heartbeat_registry: dict = {}

        @watchdog_ping(heartbeat_registry, key="worker")
        def process_batch(batch):
            ...

        # supervisor checks: time.time() - heartbeat_registry["worker"] < 30
    """

    def decorator(func):
        reg_key = key or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            registry[reg_key] = time.time()
            return func(*args, **kwargs)

        return wrapper

    return decorator


def health_check(on_failure=None):
    """
    Mark a function as a health-check endpoint.
    If it raises, *on_failure* is called with the exception (default: print).
    Returns ``True`` on success and ``False`` on failure — never re-raises.

    :param on_failure: ``Callable[[Exception], None]``.

    e.g.::

        @health_check(on_failure=lambda e: logger.error(str(e)))
        def check_db_connection():
            db.ping()
    """
    _handler = on_failure if callable(on_failure) else lambda e: print(f"[HEALTH] FAIL: {e}")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
                return True
            except Exception as exc:
                _handler(exc)
                return False

        return wrapper

    return decorator


def alert_on_failure(handler):
    """
    Call *handler* with the raised exception if the function fails,
    then re-raise so the caller still sees the error.

    :param handler: ``Callable[[Exception], None]`` — receives the exception.

    e.g.::

        @alert_on_failure(lambda e: send_slack_alert(str(e)))
        def critical_job():
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                handler(exc)
                raise

        return wrapper

    return decorator


def rate_limit(calls: int, period: float):
    """
    Raise ``RuntimeError`` if the function is called more than *calls* times
    within any rolling *period*-second window.

    :param calls:  Maximum allowed calls per window.
    :param period: Window duration in seconds.

    e.g.::

        @rate_limit(calls=10, period=60.0)
        def query_external_api():
            ...
    """

    def decorator(func):
        history: list = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # prune entries outside the window
            while history and history[0] < now - period:
                history.pop(0)
            if len(history) >= calls:
                raise RuntimeError(
                    f"[RATE LIMIT] '{func.__name__}' exceeded {calls} calls "
                    f"in {period:.1f}s."
                )
            history.append(now)
            return func(*args, **kwargs)

        return wrapper

    return decorator
