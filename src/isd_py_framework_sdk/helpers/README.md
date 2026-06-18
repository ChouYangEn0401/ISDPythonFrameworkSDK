# `helpers` — 斷言 / 裝飾器 / 例外工具集

`helpers` 是三個實用工具集合的總稱：`assertions`（斷言）、`decorators`（裝飾器）、`exceptions`（自訂例外），沒有自己的業務邏輯，只負責提供跨專案共用的工具函式與型別。

## 安裝

無額外依賴，包含於核心套件：

```bash
pip install isd-py-framework-sdk
```

---

## `assertions` — 斷言工具

所有斷言成功回傳 `True`，失敗拋出 `TypeError` / `ValueError` / `KeyError`。可從 `isd_py_framework_sdk.assertions` 或各子模組精準匯入。

```python
from isd_py_framework_sdk.assertions import (
    # 型別斷言
    assert__is_str, assert__is_int, assert__is_float, assert__is_number,
    assert__is_bool, assert__is_dict, assert__is_list, assert__is_tuple,
    assert__is_set, assert__is_callable, assert__is_none, assert__is_not_none,
    assert__is_instance, assert__is_subclass,
    # 複合型別斷言
    assert__is_list_of_str, assert__is_list_of_int, assert__is_list_of_float,
    assert__is_list_of_number, assert__is_list_of_list_of_str,
    assert__is_list_of_tuple_of_str, assert__is_dict_of_str_to_str,
    # 值域斷言
    assert__is_positive, assert__is_non_negative, assert__is_not_empty,
    assert__in_range, assert__is_one_of, assert__matches_pattern,
    # 集合斷言
    assert__has_length, assert__min_length, assert__max_length,
    assert__all_keys_exist, assert__is_unique, assert__no_none_values,
)
```

### 型別斷言 (`type_assertions`)

| 函式 | 說明 |
|---|---|
| `assert__is_str(obj)` | 必須是 `str` |
| `assert__is_int(obj)` | 必須是 `int`（`bool` 排除） |
| `assert__is_float(obj)` | 必須是 `float` |
| `assert__is_number(obj)` | 必須是 `int \| float`（`bool` 排除） |
| `assert__is_bool(obj)` | 必須是 `bool` |
| `assert__is_dict(obj)` | 必須是 `dict` |
| `assert__is_list(obj)` | 必須是 `list` |
| `assert__is_tuple(obj)` | 必須是 `tuple` |
| `assert__is_set(obj)` | 必須是 `set` |
| `assert__is_callable(obj)` | 必須是 callable |
| `assert__is_none(obj)` | 必須是 `None` |
| `assert__is_not_none(obj)` | 不得為 `None` |
| `assert__is_instance(obj, cls)` | `isinstance` 檢查 |
| `assert__is_subclass(cls, parent)` | `issubclass` 檢查 |
| `assert__is_list_of_str(obj)` | `list[str]` |
| `assert__is_list_of_int(obj)` | `list[int]` |
| `assert__is_list_of_float(obj)` | `list[float]` |
| `assert__is_list_of_number(obj)` | `list[int \| float]` |
| `assert__is_list_of_list_of_str(obj)` | `list[list[str]]` |
| `assert__is_list_of_tuple_of_str(obj)` | `list[tuple[str, ...]]` |
| `assert__is_dict_of_str_to_str(obj)` | `dict[str, str]` |

### 值域斷言 (`value_assertions`)

| 函式 | 說明 |
|---|---|
| `assert__is_positive(obj)` | 必須 > 0 |
| `assert__is_non_negative(obj)` | 必須 >= 0 |
| `assert__is_not_empty(obj)` | 不得為 `None` 或空容器/字串 |
| `assert__in_range(obj, low, high, *, inclusive=True)` | 值域範圍檢查 |
| `assert__is_one_of(obj, options)` | 成員資格檢查 |
| `assert__matches_pattern(obj, pattern)` | 正規表達式全匹配 |

### 集合斷言 (`collection_assertions`)

| 函式 | 說明 |
|---|---|
| `assert__has_length(obj, n)` | `len(obj) == n` |
| `assert__min_length(obj, n)` | `len(obj) >= n` |
| `assert__max_length(obj, n)` | `len(obj) <= n` |
| `assert__all_keys_exist(d, keys)` | dict 必須包含所有指定 keys |
| `assert__is_unique(obj)` | 元素不得重複 |
| `assert__no_none_values(obj)` | 不得含有 `None` 值 |

```python
assert__is_int(42)                          # OK
assert__is_number(3.14)                      # OK
assert__is_not_empty(["a", "b"])             # OK
assert__in_range(5, 1, 10)                   # OK
assert__is_one_of("dark", ["dark", "light"]) # OK
assert__all_keys_exist({"a": 1, "b": 2}, ["a", "b"])  # OK
assert__matches_pattern("abc-123", r"[a-z]+-\d+")     # OK
```

---

## `decorators` — 裝飾器工具

所有裝飾器可從 `isd_py_framework_sdk.decorators` 匯入，也可從各子模組精準匯入（保留完整路徑）：

```python
from isd_py_framework_sdk.decorators import function_timer, retry, etl_step, ...
from isd_py_framework_sdk.helpers.decorators.profiling import log_call
```

### Profiling — 計時 / 呼叫計數 / 記憶體

| 裝飾器 | 說明 |
|---|---|
| `@function_timer` | 印出函式執行時間（wall-clock）|
| `@timed_and_conditional_return` | 計時；傳入 `with_time_return=True` 回傳 `(result, elapsed)` |
| `@log_call(show_args, show_return)` | 在每次呼叫前後印出函式名稱、參數、回傳值 |
| `@count_calls` | 累計呼叫次數，結果存在 `func.call_count` |
| `@profile_memory` | 以 `tracemalloc` 測量記憶體峰值，印出每次呼叫的差量 KB |

```python
from isd_py_framework_sdk.decorators import function_timer, timed_and_conditional_return, log_call, count_calls, profile_memory

@function_timer
def slow_task():
    import time; time.sleep(0.1)

@timed_and_conditional_return
def measured():
    return 42

result = measured()                                # → 42
result, elapsed = measured(with_time_return=True)  # → (42, 0.000…)

@log_call(show_args=True, show_return=True)
def add(a, b):
    return a + b

@count_calls
def ping(): ...
ping(); ping()
print(ping.call_count)  # 2

@profile_memory
def load_big_file(path): ...
```

### Lifecycle — API 版本標記

| 裝飾器 | 說明 |
|---|---|
| `@test_func(reason)` | 每次呼叫發出 `TestFuncWarning` |
| `@old_method(reason)` | 每次呼叫發出 `OldFuncWarning` |
| `@deprecated(reason)` | 每次呼叫發出 `DeprecationWarning` |
| `@battered(reason)` | 每次呼叫發出 `UserWarning`（強調易崩潰）|
| `@experimental(reason)` | **第一次**呼叫發出 `FutureWarning`（API 不穩定）|
| `@removed_in(version, reason)` | 每次呼叫提示將在 *version* 版本移除 |
| `@since(version)` | 靜態標記，說明此 API 自 *version* 起引入，無運行期副作用 |

```python
from isd_py_framework_sdk.decorators import test_func, old_method, deprecated, battered, experimental, removed_in, since

@deprecated("Use `new_func` instead.")
def old_func(): ...

@experimental("Behaviour may change in v2.")
def new_feature(): ...

@removed_in("2.0.0", reason="Use `new_api()` instead.")
def legacy_api(): ...

@since("1.3.0")
def stable_feature(): ...
```

### Control Flow — 流程控制

| 裝飾器 | 說明 |
|---|---|
| `@retry(max_attempts, delay, backoff, exceptions)` | 自動重試，支援延遲與指數退避 |
| `@once` | 只執行一次，後續呼叫直接回傳快取結果 |
| `@suppress_exceptions(*exc, default, log)` | 攔截指定例外，回傳 `default` 值 |
| `@throttle(interval)` | 節流：同一函式每 *interval* 秒最多觸發一次 |
| `@timeout(seconds)` | 超過指定秒數拋 `TimeoutError` |

```python
from isd_py_framework_sdk.decorators import retry, once, suppress_exceptions, throttle, timeout

@retry(max_attempts=5, delay=1.0, backoff=2.0, exceptions=(IOError,))
def fetch(): ...  # 最多重試 5 次，延遲 1→2→4→8 秒

@suppress_exceptions(ZeroDivisionError, default=-1, log=True)
def safe_div(a, b): return a / b
# safe_div(1, 0) → -1

@throttle(2.0)
def heartbeat(): ...  # 2 秒內只執行一次

@timeout(5.0)
def slow_call(): ...  # 超過 5 秒拋 TimeoutError
```

### Concurrency — 併發工具

| 裝飾器 | 說明 |
|---|---|
| `@run_in_thread` | 在 daemon thread 中執行，立即回傳 `Thread` 物件 |
| `@synchronized` / `@synchronized(lock)` | 以 `Lock` 串列化存取，可多函式共用同一把鎖 |

```python
from isd_py_framework_sdk.decorators import run_in_thread, synchronized
import threading

@run_in_thread
def bg_task():
    import time; time.sleep(2)

t = bg_task()   # 非阻塞，立即回傳
t.join()

shared_lock = threading.Lock()

@synchronized(shared_lock)
def write_a(): ...

@synchronized(shared_lock)
def write_b(): ...  # write_a 與 write_b 互斥
```

### ETL — 管線步驟標記

| 裝飾器 | 說明 |
|---|---|
| `@etl_step(name, stage)` | 印出步驟標頭/結尾及耗時；`stage` 可為 `"extract"/"transform"/"load"` |
| `@log_record_count(label)` | 函式返回後印出 `len(result)` |
| `@checkpoint(save_fn)` | 成功後呼叫 `save_fn(result)` 持久化；失敗只警告不中斷 |
| `@skip_on_empty` | 若第一個引數為空容器（`len == 0`）則直接回傳 `None` |
| `@idempotent_load` | 以引數 hash 快取結果；相同引數不重複執行 |

```python
from isd_py_framework_sdk.decorators import etl_step, log_record_count, checkpoint, skip_on_empty, idempotent_load

@etl_step(name="Load Users", stage="extract")
def load_users(path): return open(path).readlines()

@log_record_count("rows")
def transform(rows): return [r.strip() for r in rows]

def save_parquet(df): df.to_parquet("ckpt.parquet")

@checkpoint(save_parquet)
def heavy_transform(df): ...

@skip_on_empty
def process(records): ...   # records 為空時直接回傳 None

@idempotent_load
def fetch_api(endpoint): ...  # 相同 endpoint 只呼叫一次
```

### Validation — 輸入 / 輸出防衛

| 裝飾器 | 說明 |
|---|---|
| `@not_none(*arg_names)` | 指定參數不得為 `None` |
| `@validate_args(**validators)` | 每個參數對應一個 `predicate`，失敗拋 `ValueError` |
| `@validate_return(validator, message)` | 驗證回傳值，失敗拋 `ValueError` |
| `@ensure_type(**type_map)` | 指定參數必須為指定型別 |
| `@clamp_return(low, high)` | 將數值回傳值強制限制在 `[low, high]` |
| `@non_empty_return` | 回傳值不得為空容器或 `None` |

```python
from isd_py_framework_sdk.decorators import not_none, validate_args, validate_return, ensure_type, clamp_return, non_empty_return

@not_none("user_id", "payload")
def create_record(user_id, payload): ...

@validate_args(
    age=lambda v: isinstance(v, int) and v >= 0,
    name=lambda v: isinstance(v, str) and len(v) > 0,
)
def register(name, age): ...

@ensure_type(path=str, count=int)
def read_file(path, count): ...

@clamp_return(0, 100)
def score(): return 150   # 回傳 100

@non_empty_return
def get_names(): return []  # 拋 ValueError
```

### GUI — 執行緒安全 / 防抖 / 元件助手

| 裝飾器 | 說明 |
|---|---|
| `@require_main_thread` | 非主執行緒呼叫時拋 `RuntimeError`（保護 Tkinter / Qt widget）|
| `@debounce(wait)` | 防抖：靜止 *wait* 秒後才執行，中途呼叫重置計時器 |
| `@gui_error_handler(on_error)` | 攔截 GUI handler 中的例外，呼叫 `on_error(exc)` 而非崩潰 |
| `@disable_widget_during_run(widget)` | 函式執行期間自動 disable / re-enable widget |
| `@run_after(delay_ms, scheduler)` | 延遲 *delay_ms* 毫秒後在主執行緒執行（預設用 `widget.after`）|

```python
from isd_py_framework_sdk.decorators import require_main_thread, debounce, gui_error_handler

@require_main_thread
def update_label(text):
    label.config(text=text)  # 背景執行緒呼叫此函式會立即拋錯

@debounce(0.3)
def on_search(text):
    ...  # 使用者停止輸入 0.3 秒後才觸發

@gui_error_handler(on_error=lambda e: status_bar.set(str(e)))
def on_button_click():
    risky_operation()  # 例外不會崩潰 GUI
```

### Monitoring — 指標 / Watchdog / 健康檢查

| 裝飾器 | 說明 |
|---|---|
| `@emit_metric(name, unit)` | 呼叫完成後印出（或傳送）wall-clock 耗時指標 |
| `@watchdog_ping(registry, key)` | 每次呼叫更新 `registry[key]` 為當前時間戳（確認存活）|
| `@health_check(on_failure)` | 成功回傳 `True`、失敗回傳 `False`（不重拋，適合探針）|
| `@alert_on_failure(on_alert)` | 例外時呼叫 `on_alert(exc)` 再重拋原本例外 |
| `@rate_limit(calls, period)` | 限制 *period* 秒內最多 *calls* 次；超限拋 `RuntimeError` |

```python
from isd_py_framework_sdk.decorators import emit_metric, watchdog_ping, health_check, alert_on_failure, rate_limit

heartbeat: dict = {}

@emit_metric("api.fetch_users")
def fetch_users(): ...   # [METRIC] api.fetch_users=0.0042s

@watchdog_ping(heartbeat, key="worker")
def process_batch(batch): ...   # heartbeat["worker"] = time.time()

@health_check(on_failure=lambda e: logger.error(str(e)))
def check_db():
    db.ping()   # 回傳 True / False，不拋例外

@rate_limit(calls=10, period=60)
def send_email(): ...   # 每分鐘最多 10 次
```

### AI Training — 訓練 / 推論生命週期

| 裝飾器 | 說明 |
|---|---|
| `@training_step` | 印出步驟 header/footer，例外加上 `[TRAIN STEP FAILED]` 前綴再重拋 |
| `@log_epoch` | 從引數取得 `epoch`，回傳值若為 dict 則印出各指標 |
| `@inference_only` | `self.training` 為 `True` 時拋 `RuntimeError`（PyTorch-style）|
| `@cache_predictions(maxsize)` | LRU 快取推論結果（以引數為 key）|
| `@grad_check` | 梯度傳播後警告 NaN / Inf（需 `self.parameters()`，PyTorch-style）|

```python
from isd_py_framework_sdk.decorators import training_step, log_epoch, inference_only, cache_predictions

class Trainer:
    @training_step
    def train_batch(self, batch):
        loss = self.forward(batch)
        loss.backward()
        return loss.item()

    @log_epoch
    def run_epoch(self, epoch, loader):
        ...
        return {"loss": 0.42, "acc": 0.91}  # 自動印出：[EPOCH 1] loss=0.4200  acc=0.9100

class Model:
    training = False

    @inference_only
    def predict(self, x): ...   # training=True 時拋 RuntimeError

    @cache_predictions(maxsize=256)
    def embed(self, text): ...   # 相同 text 只推論一次
```

### Architecture — SRP / 層次邊界 / 介面合約

| 裝飾器 | 說明 |
|---|---|
| `@single_responsibility(role)` | 在類別 / 函式上標記唯一職責，存為 `__srp_role__` |
| `@layer(name, allowed_imports)` | 標記所屬架構層，存為 `__arch_layer__` |
| `@interface_method` | 標記公開介面合約，存為 `func.__is_interface__ = True` |
| `@abstract_implementation(interface_name)` | 標記具體實作，存為 `func.__implements__` |
| `@no_side_effects` | 宣告純函式，默認只做文件標記（可搭配測試驗證）|
| `@sealed` | 防止子類別繼承（在建立子類別時拋 `TypeError`）|
| `@require_override` | 強制子類別覆寫（呼叫父類實作時拋 `NotImplementedError`）|
| `@enforce_srp(max_methods=10)` | 若類別方法數超過上限發出 `UserWarning` |

```python
from isd_py_framework_sdk.decorators import (
    single_responsibility, layer, interface_method,
    sealed, require_override, enforce_srp, no_side_effects,
)

@single_responsibility("Parse raw CSV rows into domain records")
@layer("domain")
class CsvParser:
    @interface_method
    def parse(self, raw: str): ...

@sealed
class FinalService:
    pass
# class Sub(FinalService): ...  →  TypeError

class IBase:
    @require_override
    def process(self): ...  # 子類若未覆寫但呼叫父類此方法 → NotImplementedError

@enforce_srp(max_methods=8)
class OverloadedClass:
    ...  # 方法超過 8 個時發出警告

@no_side_effects
def pure_add(a, b): return a + b
```

---

## `exceptions` — 自訂例外

所有例外可從 `isd_py_framework_sdk.exceptions` 匯入：

```python
from isd_py_framework_sdk.exceptions import WrongOptionException, ValidationError, DataLoadError, ...
```

### 原有例外（向下相容，API 不變）

| 例外 | 說明 |
|---|---|
| `WrongOptionException(option)` | 傳入無效的選項值 |
| `WrongImplementationException(restriction)` | 違反使用規範 |
| `UnhandledConditionError(state, value)` | 條件未被處理（未知狀態）|
| `RepeatedInitializationError()` | 物件被重複初始化 |

```python
from isd_py_framework_sdk.exceptions import (
    WrongOptionException, WrongImplementationException,
    UnhandledConditionError, RepeatedInitializationError,
)

raise WrongOptionException(option="mode_x")
raise WrongImplementationException(restriction="不可在 __init__ 中呼叫")
raise UnhandledConditionError(state=current_state, value=val)
raise RepeatedInitializationError()
```

### 依面向分類（共 10 個面向）

| 面向 | 代表例外 |
|---|---|
| Lifecycle | `NotInitializedError(target)`, `AlreadyDisposedError(target)`, `TeardownError(target, reason)` |
| Options | `MissingOptionError(key)`, `OptionConflictError(keys)`, `OptionReadOnlyError(key)`, `InvalidOptionValueError(key, value)` |
| Architecture | `AbstractMethodNotImplementedError(method)`, `InterfaceContractError`, `CircularDependencyError(components)`, `ComponentNotRegisteredError`, `ComponentAlreadyRegisteredError`, `LayerViolationError(src_layer, dst_layer)` |
| Flow Control | `ConditionNotMetError`, `ExecutionOrderError`, `FlowInterruptedError(step)`, `PipelineCancelledError(pipeline)`, `StepAbortedError`, `MaxIterationsExceededError(limit)` |
| Validation | `ConfigurationError(key)`, `ValidationError(field, reason)` |
| Runtime | `TimeoutExpiredError(operation, seconds)`, `DependencyError(dependency)`, `ReadOnlyError`, `StateError(current_state, expected_state)`, `FeatureNotSupportedError`, `ResourceExhaustedError(resource)` |
| ETL | `DataExtractionError`, `DataTransformationError`, `DataLoadError(target, reason)`, `SchemaValidationError(field, expected)`, `MissingColumnError`, `DataTypeConversionError`, `DuplicateRecordError`, `EmptyDatasetError(source)`, `DataCorruptionError(source, reason)`, `PartitionError` |
| GUI | `WidgetNotFoundError(widget_id)`, `UIStateError`, `RenderError`, `EventHandlerError`, `LayoutError`, `ThemeNotFoundError(theme_name)`, `WindowNotOpenError(window_id)`, `ScreenResolutionError` |
| Monitoring | `MetricCollectionError`, `ThresholdExceededError(metric, threshold, actual)`, `WatchdogTriggeredError(watchdog_name)`, `HealthCheckFailedError(component, reason)`, `ProbeTimeoutError`, `ObservabilityError`, `SamplingError` |
| AI Training | `ModelNotFittedError(model)`, `CheckpointNotFoundError(path)`, `TrainingInterruptedError(epoch, reason)`, `HyperparameterError`, `DatasetSplitError`, `GradientExplosionError(layer, norm)`, `GradientVanishingError(layer, norm)`, `InferenceError`, `EpochLimitReachedError`, `ModelArchitectureError` |

```python
from isd_py_framework_sdk.exceptions import (
    NotInitializedError, AlreadyDisposedError, TeardownError,
    MissingOptionError, OptionConflictError, InvalidOptionValueError,
    CircularDependencyError, LayerViolationError,
    PipelineCancelledError, MaxIterationsExceededError,
    ValidationError, ConfigurationError,
    TimeoutExpiredError, ResourceExhaustedError,
    DataLoadError, SchemaValidationError, EmptyDatasetError,
    WidgetNotFoundError, UIStateError,
    ThresholdExceededError, HealthCheckFailedError,
    ModelNotFittedError, GradientExplosionError,
)
```

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/helpers/assertions_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/decorators_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/exceptions_test.py
```

---

開發/架構細節請見 [agent.md](agent.md)。
