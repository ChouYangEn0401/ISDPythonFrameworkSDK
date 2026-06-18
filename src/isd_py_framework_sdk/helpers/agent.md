# agent.md — `helpers` 套件

## 職責

`helpers` 是三個實用工具集合的總稱，沒有自己的業務邏輯，只做匯出：

```python
# helpers/__init__.py 用 * import 匯出全部三個子套件的 __all__
from .assertions import *
from .decorators import *
from .exceptions import *
```

---

## 子套件結構

```
helpers/
├── __init__.py                    匯出全部 assertions + decorators + exceptions
├── assertions/
│   ├── __init__.py
│   ├── type_assertions.py        assert__is_*（型別系列）
│   ├── value_assertions.py       assert__is_positive, assert__in_range...（值域系列）
│   └── collection_assertions.py  assert__has_length, assert__is_unique...（集合系列）
├── decorators/
│   ├── __init__.py
│   ├── profiling.py              function_timer, log_call, count_calls, profile_memory
│   ├── lifecycle.py              deprecated, experimental, removed_in, since...
│   ├── control_flow.py           retry, once, throttle, timeout, suppress_exceptions
│   ├── concurrency.py            run_in_thread, synchronized
│   ├── etl.py                    etl_step, log_record_count, checkpoint, skip_on_empty, idempotent_load
│   ├── validation.py             not_none, validate_args, validate_return, ensure_type, clamp_return, non_empty_return
│   ├── gui.py                    require_main_thread, debounce, gui_error_handler, disable_widget_during_run, run_after
│   ├── monitoring.py             emit_metric, watchdog_ping, health_check, alert_on_failure, rate_limit
│   ├── ai_training.py            training_step, log_epoch, inference_only, cache_predictions, grad_check
│   └── architecture.py           single_responsibility, layer, interface_method, sealed, require_override, enforce_srp...
└── exceptions/
    ├── __init__.py
    ├── lifecycle.py              NotInitializedError, AlreadyDisposedError, TeardownError
    ├── options.py                MissingOptionError, OptionConflictError, OptionReadOnlyError, InvalidOptionValueError
    ├── architecture.py           AbstractMethodNotImplementedError, CircularDependencyError, LayerViolationError...
    ├── flow_control.py           PipelineCancelledError, MaxIterationsExceededError, FlowInterruptedError...
    ├── validation.py             ValidationError, ConfigurationError
    ├── runtime.py                TimeoutExpiredError, DependencyError, StateError, ResourceExhaustedError...
    ├── etl.py                    DataLoadError, SchemaValidationError, EmptyDatasetError, DataCorruptionError...
    ├── gui.py                    WidgetNotFoundError, UIStateError, ThemeNotFoundError, WindowNotOpenError...
    ├── monitoring.py             ThresholdExceededError, WatchdogTriggeredError, HealthCheckFailedError...
    └── ai_training.py            ModelNotFittedError, TrainingInterruptedError, GradientExplosionError...
```

---

## assertions — 斷言工具

所有斷言：成功回傳 `True`，失敗拋出 `TypeError` / `ValueError` / `KeyError`。

**Import：**
```python
from isd_py_framework_sdk.assertions import assert__is_str, assert__in_range, ...
# 或精準引用
from isd_py_framework_sdk.helpers.assertions.type_assertions import assert__is_str
```

**三類斷言：**

| 類別 | 檔案 | 說明 |
|---|---|---|
| 型別斷言 | `type_assertions.py` | `assert__is_str`, `assert__is_int`, `assert__is_list_of_str`...（bool 被 int 排除）|
| 值域斷言 | `value_assertions.py` | `assert__is_positive`, `assert__is_non_negative`, `assert__in_range`, `assert__is_one_of`, `assert__matches_pattern` |
| 集合斷言 | `collection_assertions.py` | `assert__has_length`, `assert__is_unique`, `assert__all_keys_exist`, `assert__contains_in_list`, `assert__contains_in_str`, `assert__contains_in_dataclass`, `assert__contains_in_object` |

**注意：**`assert__is_int` 會排除 `bool`（因為 `isinstance(True, int)` 在 Python 為 `True`，但此套件把 `bool` 視為獨立型別）。

---

## decorators — 裝飾器工具

所有裝飾器可從 `isd_py_framework_sdk.decorators` 或各子模組精準引用。

**10 個面向：**

### Profiling
| 裝飾器 | 功能 |
|---|---|
| `@function_timer` | wall-clock 計時印出 |
| `@timed_and_conditional_return` | 計時；`with_time_return=True` 回傳 `(result, elapsed)` |
| `@log_call(show_args, show_return)` | 每次呼叫印出函式名稱、參數、回傳值 |
| `@count_calls` | 累計呼叫次數存於 `func.call_count` |
| `@profile_memory` | tracemalloc 測量記憶體峰值 |

### Lifecycle
| 裝飾器 | 警告類型 |
|---|---|
| `@test_func(reason)` | `TestFuncWarning` |
| `@old_method(reason)` | `OldFuncWarning` |
| `@deprecated(reason)` | `DeprecationWarning` |
| `@battered(reason)` | `UserWarning`（強調易崩） |
| `@experimental(reason)` | `FutureWarning`（只警告一次） |
| `@removed_in(version, reason)` | 提示即將移除 |
| `@since(version)` | 靜態標記，無運行期副作用 |

### Control Flow
`@retry(max_attempts, delay, backoff, exceptions)` — 指數退避重試  
`@once` — 只執行一次，後續回傳快取  
`@suppress_exceptions(*exc, default, log)` — 捕捉後回傳 default  
`@throttle(interval)` — 節流：interval 秒最多一次  
`@timeout(seconds)` — 超時拋 `TimeoutError`

### Concurrency
`@run_in_thread` — daemon thread 非阻塞執行，回傳 `Thread`  
`@synchronized` / `@synchronized(lock)` — 以 Lock 串列化，可多函式共用同一把鎖

### ETL
`@etl_step(name, stage)` — 印步驟 header/footer 與耗時  
`@log_record_count(label)` — 印出 `len(result)`  
`@checkpoint(save_fn)` — 成功後呼叫 `save_fn(result)`  
`@skip_on_empty` — 第一個引數空容器時回傳 `None`  
`@idempotent_load` — LRU 快取（以引數 hash 為 key）

### Validation
`@not_none(*arg_names)` — 指定參數不得為 None  
`@validate_args(**validators)` — 每個參數對應 predicate  
`@validate_return(validator, message)` — 驗證回傳值  
`@ensure_type(**type_map)` — 型別強制  
`@clamp_return(low, high)` — 數值回傳值 clamp 到 [low, high]  
`@non_empty_return` — 不得回傳空容器或 None

### GUI
`@require_main_thread` — 非主執行緒呼叫時拋 `RuntimeError`  
`@debounce(wait)` — 防抖：停止 wait 秒後才執行  
`@gui_error_handler(on_error)` — 攔截 GUI 例外，呼叫 on_error(exc)  
`@disable_widget_during_run(widget)` — 執行期間 disable widget  
`@run_after(delay_ms, scheduler)` — 延遲在主執行緒執行

### Monitoring
`@emit_metric(name, unit)` — 印出 wall-clock 耗時指標  
`@watchdog_ping(registry, key)` — 更新 registry[key] = time.time()  
`@health_check(on_failure)` — 回傳 True/False，不重拋  
`@alert_on_failure(on_alert)` — 例外時呼叫 on_alert(exc) 再重拋  
`@rate_limit(calls, period)` — 限制 period 秒內最多 calls 次

### AI Training
`@training_step` — 印 header/footer，失敗加 [TRAIN STEP FAILED] 前綴  
`@log_epoch` — 從引數取 epoch，回傳 dict 時印出各指標  
`@inference_only` — self.training==True 時拋 RuntimeError  
`@cache_predictions(maxsize)` — LRU 推論快取  
`@grad_check` — 警告 NaN/Inf 梯度（PyTorch-style）

### Architecture
`@single_responsibility(role)` — 設 `__srp_role__`，靜態標記  
`@layer(name, allowed_imports)` — 設 `__arch_layer__`  
`@interface_method` — 設 `func.__is_interface__ = True`  
`@abstract_implementation(interface_name)` — 設 `func.__implements__`  
`@no_side_effects` — 宣告純函式（文件標記）  
`@sealed` — 防止子類繼承，建立子類時拋 `TypeError`  
`@require_override` — 強制子類覆寫，父類實作呼叫時拋 `NotImplementedError`  
`@enforce_srp(max_methods=10)` — 方法數超限時 `UserWarning`

---

## exceptions — 自訂例外

**Import：**
```python
from isd_py_framework_sdk.exceptions import ValidationError, DataLoadError, ...
```

**10 個面向，共 50+ 個例外類別：**

| 面向 | 代表例外 |
|---|---|
| Legacy（向下相容）| `WrongOptionException`, `WrongImplementationException`, `UnhandledConditionError`, `RepeatedInitializationError` |
| Lifecycle | `NotInitializedError`, `AlreadyDisposedError`, `TeardownError` |
| Options | `MissingOptionError`, `OptionConflictError`, `InvalidOptionValueError` |
| Architecture | `CircularDependencyError`, `LayerViolationError`, `ComponentNotRegisteredError` |
| Flow Control | `PipelineCancelledError`, `MaxIterationsExceededError`, `FlowInterruptedError` |
| Validation | `ValidationError`, `ConfigurationError` |
| Runtime | `TimeoutExpiredError`, `DependencyError`, `StateError`, `ResourceExhaustedError` |
| ETL | `DataLoadError`, `SchemaValidationError`, `EmptyDatasetError`, `DataCorruptionError` |
| GUI | `WidgetNotFoundError`, `UIStateError`, `ThemeNotFoundError`, `WindowNotOpenError` |
| Monitoring | `ThresholdExceededError`, `WatchdogTriggeredError`, `HealthCheckFailedError` |
| AI Training | `ModelNotFittedError`, `TrainingInterruptedError`, `GradientExplosionError`, `GradientVanishingError` |

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/helpers/assertions_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/decorators_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/exceptions_test.py
```
