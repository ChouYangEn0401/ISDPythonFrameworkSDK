"""
Quick smoke-test for helpers/decorators
Run: python src/isd_py_framework_sdk/helpers/decorators/_test.py
"""

import sys
import time
import threading
import warnings

sys.path.insert(0, "src")

from isd_py_framework_sdk.decorators import (
    # profiling
    function_timer, timed_and_conditional_return, log_call, count_calls, profile_memory,
    # lifecycle
    deprecated, battered, experimental, removed_in, since,
    # control-flow
    retry, once, suppress_exceptions, throttle, timeout,
    # concurrency
    run_in_thread, synchronized,
    # ETL
    etl_step, log_record_count, checkpoint, skip_on_empty, idempotent_load,
    # validation
    not_none, validate_args, validate_return, ensure_type, clamp_return, non_empty_return,
    # GUI
    require_main_thread, debounce, gui_error_handler,
    # monitoring
    emit_metric, watchdog_ping, health_check, alert_on_failure, rate_limit,
    # AI training
    training_step, log_epoch, inference_only, cache_predictions,
    # architecture
    single_responsibility, layer, interface_method, no_side_effects,
    sealed, require_override, enforce_srp,
)

PASS = 0
FAIL = 0


def ok(label: str):
    global PASS
    PASS += 1
    print(f"  ✔  {label}")


def fail(label: str, exc: Exception):
    global FAIL
    FAIL += 1
    print(f"  ✘  {label}  →  {type(exc).__name__}: {exc}")


def expect_pass(label: str, fn):
    try:
        result = fn()
        if result is False:
            fail(label, Exception("assertion returned False"))
        else:
            ok(label)
    except Exception as e:
        fail(label, e)


def expect_fail(label: str, fn, exc_type=Exception):
    try:
        fn()
        fail(label, Exception("no exception raised"))
    except exc_type:
        ok(label)
    except Exception as e:
        fail(label, e)


def chk(label: str, condition: bool):
    """Simple boolean-check shorthand."""
    if condition:
        ok(label)
    else:
        fail(label, Exception("condition was False"))


# ──────────────────────────────────────────────────────────────────────────────
print("\n── Profiling ────────────────────────────────────────────────────────────")

@function_timer
def _add(a, b): return a + b

chk("function_timer: runs & returns value", _add(1, 2) == 3)

@timed_and_conditional_return
def _mul(a, b): return a * b

chk("timed_and_conditional_return: normal return", _mul(3, 4) == 12)
chk("timed_and_conditional_return: with_time_return=True", isinstance(_mul(2, 3, with_time_return=True), tuple))

@log_call(show_args=True, show_return=True)
def _greet(name): return f"Hi {name}"

chk("log_call: returns value", _greet("test") == "Hi test")

@count_calls
def _ping(): return "pong"

_ping(); _ping(); _ping()
chk("count_calls: count == 3", _ping.call_count == 3)

@profile_memory
def _alloc(): return [0] * 1000

expect_pass("profile_memory: runs without error", lambda: _alloc())

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Lifecycle ────────────────────────────────────────────────────────────")

@deprecated("use new_func")
def _old(): return 1

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    _old()
    chk("deprecated: DeprecationWarning issued", any(issubclass(x.category, DeprecationWarning) for x in w))

@battered("fragile")
def _fragile(): return 2

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    _fragile()
    chk("battered: UserWarning issued", any(issubclass(x.category, UserWarning) for x in w))

@experimental("unstable")
def _new_feat(): return 3

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    _new_feat(); _new_feat()
    fut = [x for x in w if issubclass(x.category, FutureWarning)]
    chk("experimental: FutureWarning only on first call", len(fut) == 1)

@removed_in("2.0.0", reason="use v2 api")
def _legacy(): return 4

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    _legacy()
    chk("removed_in: DeprecationWarning issued", any(issubclass(x.category, DeprecationWarning) for x in w))

@since("1.0.0")
def _stable(): return 5

chk("since: no warning, returns value", _stable() == 5)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Control Flow ─────────────────────────────────────────────────────────")

_attempt = [0]

@retry(max_attempts=3, delay=0, exceptions=(ValueError,))
def _flaky():
    _attempt[0] += 1
    if _attempt[0] < 3:
        raise ValueError("not yet")
    return "ok"

_attempt[0] = 0
chk("retry: succeeds on 3rd attempt", _flaky() == "ok")

_attempt[0] = 0
@retry(max_attempts=2, delay=0, exceptions=(ValueError,))
def _always_fails():
    raise ValueError("always")

expect_fail("retry: raises after max_attempts", lambda: _always_fails(), ValueError)

@once
def _init():
    _init.calls = getattr(_init, "calls", 0) + 1
    return "initialized"

_init()
_init()
chk("once: executes once, returns cached", _init.calls == 1 and _init() == "initialized")

@suppress_exceptions(ZeroDivisionError, default=-1, log=False)
def _div(a, b): return a / b

chk("suppress_exceptions: returns default on error", _div(1, 0) == -1)
chk("suppress_exceptions: passes through on success", _div(10, 2) == 5.0)

@throttle(0.1)
def _throttled(): return time.time()

t1 = _throttled()
t2 = _throttled()
chk("throttle: second call within window skipped (None)", t2 is None)
time.sleep(0.15)
t3 = _throttled()
chk("throttle: after window passes, executes again", t3 is not None)

@timeout(0.5)
def _fast(): return 42

chk("timeout: fast function returns normally", _fast() == 42)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Concurrency ──────────────────────────────────────────────────────────")

results = []

@run_in_thread
def _bg():
    time.sleep(0.05)
    results.append("done")

t = _bg()
chk("run_in_thread: returns Thread", isinstance(t, threading.Thread))
t.join()
chk("run_in_thread: thread body executed", results == ["done"])

counter = [0]

@synchronized
def _inc():
    counter[0] += 1

threads = [threading.Thread(target=_inc) for _ in range(50)]
for th in threads: th.start()
for th in threads: th.join()
chk("synchronized: counter == 50 (no race)", counter[0] == 50)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── ETL ──────────────────────────────────────────────────────────────────")

@etl_step(name="Load", stage="extract")
def _extract(path): return [1, 2, 3]

chk("etl_step: returns result", _extract("x") == [1, 2, 3])

@log_record_count("rows")
def _transform(rows): return rows

chk("log_record_count: returns result", _transform([1, 2]) == [1, 2])

saved = []

@checkpoint(lambda r: saved.append(r))
def _load(data): return data

_load([10, 20])
chk("checkpoint: save_fn called with result", saved == [[10, 20]])

@skip_on_empty()
def _process(records): return [r * 2 for r in records]

chk("skip_on_empty: empty list → None", _process([]) is None)
chk("skip_on_empty: non-empty → runs", _process([1, 2]) == [2, 4])

_loaded_ids: set = set()

@idempotent_load(id_fn=lambda r: r, store=_loaded_ids)
def _fetch(key):
    return key

_fetch("a"); _fetch("a"); _fetch("b")
chk("idempotent_load: unique IDs tracked in store", len(_loaded_ids) == 2)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Validation ───────────────────────────────────────────────────────────")

@not_none("x", "y")
def _fn(x, y): return x + y

chk("not_none: valid args pass", _fn(1, 2) == 3)
expect_fail("not_none: None arg → ValueError",  lambda: _fn(None, 2), ValueError)

@validate_args(n=lambda v: isinstance(v, int) and v >= 0)
def _fact(n): return n

chk("validate_args: valid passes", _fact(5) == 5)
expect_fail("validate_args: invalid → ValueError", lambda: _fact(-1), ValueError)

@validate_return(lambda v: v > 0, message="must be positive")
def _pos_result(): return 5

chk("validate_return: valid return", _pos_result() == 5)

@validate_return(lambda v: v > 0)
def _neg_result(): return -1

expect_fail("validate_return: invalid → ValueError", lambda: _neg_result(), ValueError)

@ensure_type(name=str, count=int)
def _typed(name, count): return name * count

chk("ensure_type: correct types", _typed("x", 3) == "xxx")
expect_fail("ensure_type: wrong type → TypeError", lambda: _typed("x", "3"), TypeError)

@clamp_return(0, 100)
def _score(v): return v

chk("clamp_return: within range", _score(50) == 50)
chk("clamp_return: above max → clamped", _score(150) == 100)
chk("clamp_return: below min → clamped", _score(-10) == 0)

@non_empty_return()
def _items(flag):
    return [1, 2] if flag else []

chk("non_empty_return: non-empty passes", _items(True) == [1, 2])
expect_fail("non_empty_return: empty → ValueError", lambda: _items(False), ValueError)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── GUI ──────────────────────────────────────────────────────────────────")

@require_main_thread
def _main_only(): return True

chk("require_main_thread: main thread OK", _main_only() is True)

bg_error = []

def _bg_call():
    try:
        _main_only()
    except RuntimeError as e:
        bg_error.append(e)

t = threading.Thread(target=_bg_call)
t.start(); t.join()
chk("require_main_thread: background thread → RuntimeError", len(bg_error) == 1)

errors = []

@gui_error_handler(on_error=lambda e: errors.append(e))
def _handler():
    raise ValueError("oops")

_handler()
chk("gui_error_handler: exception captured, not re-raised", len(errors) == 1 and isinstance(errors[0], ValueError))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Monitoring ───────────────────────────────────────────────────────────")

registry = {}

@watchdog_ping(registry, key="worker")
def _worker(): return "ok"

_worker()
chk("watchdog_ping: key updated in registry", "worker" in registry and isinstance(registry["worker"], float))

@health_check(on_failure=lambda e: None)
def _healthy(): return True

@health_check(on_failure=lambda e: None)
def _sick(): raise RuntimeError("down")

chk("health_check: healthy → True", _healthy() is True)
chk("health_check: sick → False", _sick() is False)

alerted = []

@alert_on_failure(lambda e: alerted.append(e))
def _critical(): raise ValueError("boom")

expect_fail("alert_on_failure: re-raises and alerts", lambda: _critical(), ValueError)
chk("alert_on_failure: on_alert was called", len(alerted) == 1)

@emit_metric("test.op")
def _measured(): return 99

chk("emit_metric: returns value", _measured() == 99)

@rate_limit(calls=2, period=1)
def _limited(): return True

_limited(); _limited()
expect_fail("rate_limit: 3rd call in window → RuntimeError", lambda: _limited(), RuntimeError)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── AI Training ──────────────────────────────────────────────────────────")

class _FakeTrainer:
    training = False

    @training_step
    def step(self, x):
        return x * 2

    @log_epoch
    def epoch(self, epoch, loader=None):
        return {"loss": 0.5, "acc": 0.9}

    @inference_only
    def predict(self, x):
        return x

    @cache_predictions(maxsize=8)
    def embed(self, text):
        self._embed_calls = getattr(self, "_embed_calls", 0) + 1
        return f"vec:{text}"

trainer = _FakeTrainer()
chk("training_step: executes & returns", trainer.step(5) == 10)
chk("log_epoch: executes & returns dict", isinstance(trainer.epoch(1), dict))
chk("inference_only: training=False passes", trainer.predict(3) == 3)

trainer.training = True
expect_fail("inference_only: training=True → RuntimeError", lambda: trainer.predict(3), RuntimeError)
trainer.training = False

trainer.embed("hello"); trainer.embed("hello"); trainer.embed("world")
chk("cache_predictions: same arg not re-computed", trainer._embed_calls == 2)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Architecture / SRP ───────────────────────────────────────────────────")

@single_responsibility("Parse raw CSV rows into domain records")
class _CsvParser:
    pass

chk("single_responsibility: __srp_role__ set", _CsvParser.__srp_role__ == "Parse raw CSV rows into domain records")
expect_fail("single_responsibility: empty role → AssertionError", lambda: single_responsibility("")(lambda: None), AssertionError)

@layer("domain")
def _calc(x): return x

chk("layer: __arch_layer__ set", _calc.__arch_layer__ == "domain")

@interface_method
def _iface(self): ...

chk("interface_method: __is_interface__ set", _iface.__is_interface__ is True)

@no_side_effects()
def _pure(a, b): return a + b

chk("no_side_effects: runs normally", _pure(1, 2) == 3)

@sealed
class _Final:
    pass

expect_fail("sealed: subclassing → TypeError", lambda: type("_Sub", (_Final,), {}), TypeError)

class _IBase:
    @require_override
    def process(self): ...

expect_fail("require_override: calling base → NotImplementedError", lambda: _IBase().process(), NotImplementedError)

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    @enforce_srp({"a": "does A", "ghost": "missing method"})
    class _ManifestClass:
        def a(self): ...
    chk("enforce_srp: UserWarning for missing role method",
        any(issubclass(x.category, UserWarning) for x in w))
chk("enforce_srp: __srp_manifest__ attached", hasattr(_ManifestClass, "__srp_manifest__"))

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  結果：{PASS} PASS  /  {FAIL} FAIL")
if FAIL:
    print("  ⚠  有測試失敗，請檢查上方輸出。")
else:
    print("  🎉 全部通過！")
print("=" * 60)
