"""
ETL decorators — mark, log, validate, and checkpoint ETL pipeline stages.
"""

import functools
import time


def etl_step(name: str = "", stage: str = ""):
    """
    Mark a function as a named ETL step.
    Prints stage header/footer and total elapsed time.

    :param name:  Human-readable step name (defaults to function name).
    :param stage: ``"extract"`` | ``"transform"`` | ``"load"`` (or any label).

    e.g.::

        @etl_step(name="Load Users", stage="extract")
        def load_users(path):
            ...
    """

    def decorator(func):
        label = name or func.__name__
        stage_tag = f" [{stage.upper()}]" if stage else ""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[ETL{stage_tag}] ▶ {label}")
            t0 = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - t0
            print(f"[ETL{stage_tag}] ✔ {label}  ({elapsed:.2f}s)")
            return result

        return wrapper

    return decorator


def log_record_count(label: str = "records"):
    """
    After the function returns, print the length of the result to track throughput.
    Works with any object that supports ``len()``.

    :param label: Description of the unit (e.g. ``"rows"``, ``"events"``).

    e.g.::

        @log_record_count("rows")
        def extract_data(path):
            return pd.read_csv(path)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                count = len(result)
                print(f"[ETL] {func.__name__}  → {count} {label}")
            except TypeError:
                pass
            return result

        return wrapper

    return decorator


def checkpoint(save_fn):
    """
    Persist the function's result via *save_fn* after a successful run.
    If *save_fn* raises, the exception is printed but **not** re-raised,
    so pipeline execution continues.

    :param save_fn: ``Callable[[result], None]`` — receives the return value.

    e.g.::

        def to_parquet(df):
            df.to_parquet("checkpoint.parquet")

        @checkpoint(to_parquet)
        def transform(df):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                save_fn(result)
                print(f"[CHECKPOINT] {func.__name__} saved.")
            except Exception as exc:
                print(f"[CHECKPOINT] {func.__name__} save failed: {exc}")
            return result

        return wrapper

    return decorator


def skip_on_empty(empty_return=None):
    """
    Skip execution and return *empty_return* when the first positional argument
    is falsy (``None``, empty list, empty DataFrame, …).

    Useful for short-circuiting transform/load steps when upstream produced nothing.

    :param empty_return: Value to return when input is empty (default: ``None``).

    e.g.::

        @skip_on_empty(empty_return=[])
        def transform(rows):
            ...
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            first = args[0] if args else None
            is_empty = first is None or (hasattr(first, "__len__") and len(first) == 0)
            if is_empty:
                print(f"[ETL] {func.__name__} skipped — empty input.")
                return empty_return
            return func(*args, **kwargs)

        return wrapper

    return decorator


def idempotent_load(id_fn, store):
    """
    Skip the load function if a record with the same ID is already present in *store*.

    :param id_fn:  ``Callable[[result], hashable]`` — extract the unique key from the output.
    :param store:  A set-like or dict-like object that supports ``__contains__`` and ``add``/``__setitem__``.

    e.g.::

        seen_ids: set = set()

        @idempotent_load(id_fn=lambda r: r["id"], store=seen_ids)
        def load_record(record):
            db.insert(record)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is not None:
                key = id_fn(result)
                if key in store:
                    print(f"[ETL] {func.__name__} — duplicate id={key!r}, skipped re-load.")
                    return result
                if isinstance(store, set):
                    store.add(key)
                else:
                    store[key] = True
            return result

        return wrapper

    return decorator
