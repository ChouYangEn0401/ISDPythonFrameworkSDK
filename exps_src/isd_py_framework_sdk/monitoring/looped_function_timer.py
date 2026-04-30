import datetime
import functools
import sys
import time
from dataclasses import dataclass
from statistics import mean
from typing import Callable, Optional, Protocol, runtime_checkable

from isd_py_framework_sdk.message_logger import (
    DarkThemeTerminalAdapter,
    LogLevelLiteral,
    SingletonSystemLogger,
)


@dataclass(frozen=False)  ## this api should be mutable, so frozen=False !!??
class ProgressState:
    processed: int
    total: int
    total_time: float
    eta_seconds: Optional[float]


ProgressMessageMaker = Callable[[ProgressState, int, bool], str]


@runtime_checkable
class ProgressLoggerProtocol(Protocol):
    def log(self, msg: str, level: str) -> None: ...
    def info(self, msg: str) -> None: ...
    def success(self, msg: str) -> None: ...
    def flush(self) -> None: ...


def _default_message_maker(state: ProgressState, bar_len: int, use_bar: bool) -> str:
    eta_str = (
        f"{state.eta_seconds:.3f}s ({str(datetime.timedelta(seconds=int(state.eta_seconds))).replace(' days, ', ':')})"
        if state.eta_seconds is not None
        else "N/A"
    )

    if use_bar:
        ratio = min(max(state.processed / state.total, 0), 1)
        filled_len = int(bar_len * ratio)
        bar_str = f"{'█' * filled_len}{'-' * (bar_len - filled_len)}"
        return (
            f"[{bar_str}] {state.processed:>3,}/{state.total:<3,} "
            f"TRT={state.total_time:.3f}s ETA={eta_str}"
        )

    return (
        f"Progress: {state.processed:12.0f}/{state.total}, "
        f"TRT={state.total_time:.3f}s, ETA={eta_str}"
    )


class LoopedFunctionTimer:
    @property
    def count(self):
        return len(self._time_records)

    @property
    def last(self):
        return self._time_records[-1] if self._time_records else None

    @property
    def avg(self):
        return mean(self._time_records) if self._time_records else None

    @property
    def sum(self):
        return self._total_time

    def __init__(
        self,
        total: Optional[int] = None,
        inline: bool = True,
        level: LogLevelLiteral = "INFO",
        logger: Optional[ProgressLoggerProtocol] = None,
        message_maker: Optional[ProgressMessageMaker] = None,
    ):
        self._total = total
        self.reset()

        self._start_time = None
        self._time_records = []
        self._total_time = 0
        self._inline = inline
        self._level = level
        self._last_processed = 0

        self.update_interval = max(
            1,
            min(int(self._total * 0.01) if self._total else 10000, 10000),
        )

        self._message_maker = message_maker or _default_message_maker
        self.logger = logger or SingletonSystemLogger()

        if isinstance(self.logger, SingletonSystemLogger):
            if getattr(self.logger, "adapters", None) is not None and not self.logger.adapters:
                self.logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    def reset_total(self, total: int):
        self._total = total

    def reset(self):
        self._start_time = None
        self._time_records = []
        self._total_time = 0

    def start(self):
        self._start_time = time.perf_counter()

    def stop(self):
        if self._start_time is None:
            raise RuntimeError("Timer not started.")
        elapsed = time.perf_counter() - self._start_time
        self._time_records.append(elapsed)
        self._total_time += elapsed
        self._start_time = None
        return elapsed

    def restart(self, b_do_reset: bool = False):
        self.stop()
        if b_do_reset:
            self.reset()
        self.start()

    def eta(self, processed: int, total: Optional[int] = None, b_accurate=False):
        if processed == 0 or not self._time_records:
            return None

        total = total if total is not None else self._total
        if total is None:
            return None

        avg_per_item = self.avg
        remaining = total - processed
        if remaining <= 0 or avg_per_item is None:
            return 0.0

        remaining_time = remaining * avg_per_item
        if b_accurate and self._start_time:
            remaining_time -= (time.perf_counter() - self._start_time)

        return remaining_time

    def msg(
        self,
        processed: int,
        total: Optional[int] = None,
        inline: Optional[bool] = None,
        bar: bool = False,
        bar_len: int = 30,
        level: Optional[LogLevelLiteral] = None,
        force: bool = False,
    ):
        total = total or self._total
        inline = self._inline if inline is None else inline

        if not total:
            raise ValueError("Total is required for progress bar.")

        eta_val = self.eta(processed, total)

        if not force and processed != total:
            if processed - self._last_processed < self.update_interval:
                return
        self._last_processed = processed

        active_level = level or self._level

        state = ProgressState(
            processed=processed,
            total=total,
            total_time=self._total_time,
            eta_seconds=eta_val,
        )
        text = self._message_maker(state, bar_len, bar)

        if inline:
            sys.stdout.write("\r" + text)
            sys.stdout.flush()
            if processed == total:
                sys.stdout.write("\n")
        else:
            self.logger.log(text, active_level)

    def last_msg(
        self,
        inline: Optional[bool] = None,
        bar: bool = False,
        bar_len: int = 30,
        level: Optional[LogLevelLiteral] = None,
    ):
        self.msg(self._total, self._total, inline, bar, bar_len, level, force=True)

    def end_msg(self):
        self.logger.success("DONE")

    def show_info(self, b_clean_progress_bar=False):
        if b_clean_progress_bar:
            sys.stdout.write("\r" + " " * 120 + "\r")
            sys.stdout.flush()

        if self.avg:
            msg = (
                f"\n✅ 所有任務完成！\n\t總任務： {self._total}, "
                f"總耗時: {self.sum:.3f}s, 平均單次耗時: {self.avg:.3f}s"
            )
        else:
            msg = (
                f"\n✅ 所有任務完成！\n\t總任務： {self._total}, "
                f"總耗時: {self.sum:.3f}s, 平均單次耗時: N/A"
            )

        self.logger.info(msg)
        self.logger.info("-" * 50)
        self.logger.flush()


class MultiProcessLoopedFunctionTimer(LoopedFunctionTimer):
    def __init__(
        self,
        total: int = None,
        inline: bool = True,
        level: LogLevelLiteral = "INFO",
        logger: Optional[ProgressLoggerProtocol] = None,
        message_maker: Optional[ProgressMessageMaker] = None,
    ):
        super().__init__(total, inline, level, logger, message_maker)
        self._processed_count = 0
        self._last_update_count = 0
        self.update_interval = max(
            1,
            min(int(self._total * 0.01) if self._total else 10000, 10000),
        )

    def batched_task_completed(self, batch_size, b_show_msg: bool = True, **kwargs):
        self._processed_count += batch_size

        if (
            self._processed_count - self._last_update_count < self.update_interval
            and self._processed_count != self._total
        ):
            return

        self._last_update_count = self._processed_count

        if self._start_time is not None:
            current_total_time = time.perf_counter() - self._start_time
        else:
            current_total_time = 0

        self._total_time = current_total_time

        if self._processed_count > 0:
            avg_item_time = current_total_time / self._processed_count
            self._time_records = [avg_item_time]
        else:
            self._time_records = []

        if b_show_msg:
            self.msg(self._processed_count, total=self._total, **kwargs)

    def task_completed(self, b_show_msg: bool = True, **kwargs):
        self.batched_task_completed(1, b_show_msg, **kwargs)

    def stop(self):
        if self._start_time is None:
            return None
        elapsed = time.perf_counter() - self._start_time
        self._total_time = elapsed
        self._start_time = None
        if self._processed_count > 0:
            avg_item_time = elapsed / self._processed_count
            self._time_records = [avg_item_time]
        return elapsed


def LoopedFunction_timer_decorator(func=None, *, timer: "LoopedFunctionTimer" = None):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            t = None
            if args and hasattr(args[0], "timer"):
                t = args[0].timer
            elif timer:
                t = timer
            else:
                raise ValueError("No timer found for this function")

            t.start()
            result = f(*args, **kwargs)
            t.stop()
            t.msg(t.count, bar=True)
            return result

        return wrapper

    if func:
        return decorator(func)
    return decorator
