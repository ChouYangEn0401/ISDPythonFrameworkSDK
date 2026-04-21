"""
AI / ML training decorators — training step logging, gradient clipping guards,
inference mode enforcement, and prediction caching.
"""

import functools
import time


def training_step(func):
    """
    Mark a method as a training step.
    Logs step start/end with wall-clock time and catches/re-raises exceptions
    with a clear ``[TRAIN STEP FAILED]`` prefix.

    e.g.::

        @training_step
        def train_batch(self, batch):
            loss = self.forward(batch)
            loss.backward()
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[TRAIN] ▶ {func.__name__}")
        t0 = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            raise RuntimeError(
                f"[TRAIN STEP FAILED] {func.__name__}: {exc}"
            ) from exc
        elapsed = time.perf_counter() - t0
        print(f"[TRAIN] ✔ {func.__name__}  ({elapsed:.4f}s)")
        return result

    return wrapper


def log_epoch(func):
    """
    Log epoch number (passed as ``epoch`` kwarg or first positional arg after ``self``)
    together with any scalar metrics in the return dict.

    e.g.::

        @log_epoch
        def run_epoch(self, epoch, loader):
            ...
            return {"loss": 0.42, "acc": 0.91}
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        epoch = kwargs.get("epoch") or (args[1] if len(args) > 1 else "?")
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        if isinstance(result, dict):
            metrics_str = "  ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in result.items())
            print(f"[EPOCH {epoch}]  {metrics_str}  ({elapsed:.2f}s)")
        else:
            print(f"[EPOCH {epoch}]  done  ({elapsed:.2f}s)")
        return result

    return wrapper


def inference_only(func):
    """
    Guard that the decorated method is not called during training mode.
    Checks ``self.training`` (PyTorch-style) or ``self._training`` if present.
    Raises ``RuntimeError`` when training mode is active.

    e.g.::

        @inference_only
        def predict(self, x):
            ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0] if args else None
        training_flag = (
            getattr(self, "training", None)
            or getattr(self, "_training", None)
        )
        if training_flag:
            raise RuntimeError(
                f"[INFERENCE] '{func.__name__}' must not be called in training mode. "
                "Call model.eval() first."
            )
        return func(*args, **kwargs)

    return wrapper


def cache_predictions(maxsize: int = 128):
    """
    LRU-cache the return value of an inference function keyed on its arguments.
    Avoids recomputing predictions for repeated identical inputs.

    :param maxsize: Maximum number of cached entries (default: 128).

    .. note::

        Arguments must be hashable. Use ``frozenset`` or ``tuple`` wrappers for
        array-like inputs.

    e.g.::

        @cache_predictions(maxsize=256)
        def predict_label(feature_tuple):
            ...
    """

    def decorator(func):
        from functools import lru_cache

        cached = lru_cache(maxsize=maxsize)(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # lru_cache doesn't support kwargs → convert to positional
            if kwargs:
                raise TypeError(
                    f"[cache_predictions] '{func.__name__}' does not support keyword "
                    "arguments when caching is enabled."
                )
            return cached(*args)

        wrapper.cache_info = cached.cache_info
        wrapper.cache_clear = cached.cache_clear
        return wrapper

    return decorator


def grad_check(max_norm: float = 1e6):
    """
    Check that no gradient parameter exceeds *max_norm* after the decorated
    backward/update step. Raises ``FloatingPointError`` on explosion.

    Works with PyTorch tensors (``param.grad.data.norm()``); silently skips
    if the framework is not available.

    :param max_norm: Threshold above which gradient explosion is declared.

    e.g.::

        @grad_check(max_norm=10.0)
        def optimizer_step(self):
            self.optimizer.step()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            self = args[0] if args else None
            params = getattr(self, "parameters", None)
            if callable(params):
                try:
                    import math

                    total_norm = math.sqrt(
                        sum(
                            p.grad.data.norm() ** 2
                            for p in params()
                            if p.grad is not None
                        )
                    )
                    if total_norm > max_norm:
                        raise FloatingPointError(
                            f"[GRAD CHECK] Gradient norm {total_norm:.2e} "
                            f"exceeds threshold {max_norm:.2e}."
                        )
                except (ImportError, AttributeError):
                    pass
            return result

        return wrapper

    return decorator
