"""
Quick smoke-test for helpers/exceptions
Run: python src/hyper_framework/helpers/exceptions/_test.py
"""

import sys

sys.path.insert(0, "src")

from hyper_framework.helpers.exceptions import (
    # legacy (backward-compat)
    WrongOptionException,
    WrongImplementationException,
    UnhandledConditionError,
    RepeatedInitializationError,
    # lifecycle
    NotInitializedError,
    AlreadyDisposedError,
    TeardownError,
    # options
    MissingOptionError,
    OptionConflictError,
    OptionReadOnlyError,
    InvalidOptionValueError,
    # architecture
    AbstractMethodNotImplementedError,
    InterfaceContractError,
    CircularDependencyError,
    ComponentNotRegisteredError,
    ComponentAlreadyRegisteredError,
    LayerViolationError,
    # flow control
    ConditionNotMetError,
    ExecutionOrderError,
    FlowInterruptedError,
    PipelineCancelledError,
    StepAbortedError,
    MaxIterationsExceededError,
    # validation
    ConfigurationError,
    ValidationError,
    # runtime
    TimeoutExpiredError,
    DependencyError,
    ReadOnlyError,
    StateError,
    FeatureNotSupportedError,
    ResourceExhaustedError,
    # ETL
    DataExtractionError,
    DataTransformationError,
    DataLoadError,
    SchemaValidationError,
    MissingColumnError,
    DataTypeConversionError,
    DuplicateRecordError,
    EmptyDatasetError,
    DataCorruptionError,
    PartitionError,
    # GUI
    WidgetNotFoundError,
    UIStateError,
    RenderError,
    EventHandlerError,
    LayoutError,
    ThemeNotFoundError,
    WindowNotOpenError,
    ScreenResolutionError,
    # monitoring
    MetricCollectionError,
    ThresholdExceededError,
    WatchdogTriggeredError,
    HealthCheckFailedError,
    ProbeTimeoutError,
    ObservabilityError,
    SamplingError,
    # AI training
    ModelNotFittedError,
    CheckpointNotFoundError,
    TrainingInterruptedError,
    HyperparameterError,
    DatasetSplitError,
    GradientExplosionError,
    GradientVanishingError,
    InferenceError,
    EpochLimitReachedError,
    ModelArchitectureError,
)

PASS = 0
FAIL = 0


def ok(label: str):
    global PASS
    PASS += 1
    print(f"  ✔  {label}")


def fail(label: str, note: str = ""):
    global FAIL
    FAIL += 1
    print(f"  ✘  {label}" + (f"  →  {note}" if note else ""))


def check(label: str, exc_class, raise_fn, *, is_exc=True, attr_checks: dict | None = None):
    """
    Raise the exception via *raise_fn*, then verify:
      - it is an instance of *exc_class*
      - it inherits from Exception
      - optional attribute values via *attr_checks*
    """
    try:
        raise_fn()
        fail(label, "no exception raised")
        return
    except exc_class as e:
        # verify it's an Exception subclass
        if not isinstance(e, Exception):
            fail(label, "not an Exception subclass")
            return
        # check attributes if requested
        if attr_checks:
            for attr, expected in attr_checks.items():
                actual = getattr(e, attr, "__MISSING__")
                if actual != expected:
                    fail(label, f"attr '{attr}': expected {expected!r}, got {actual!r}")
                    return
        ok(label)
    except Exception as e:
        fail(label, f"wrong exception type: {type(e).__name__}: {e}")


# ──────────────────────────────────────────────────────────────────────────────
print("\n── Legacy (backward-compat) ─────────────────────────────────────────────")

check("WrongOptionException: option attr",
      WrongOptionException,
      lambda: (_ for _ in ()).throw(WrongOptionException(option="bad_mode")),
      attr_checks={"option": "bad_mode"})

check("WrongImplementationException: restriction attr",
      WrongImplementationException,
      lambda: (_ for _ in ()).throw(WrongImplementationException(restriction="no __init__ call")),
      attr_checks={"restriction": "no __init__ call"})

check("UnhandledConditionError: kwargs in details",
      UnhandledConditionError,
      lambda: (_ for _ in ()).throw(UnhandledConditionError(mode="x", value=99)),
      attr_checks={"details": {"mode": "x", "value": 99}})

check("RepeatedInitializationError: default message",
      RepeatedInitializationError,
      lambda: (_ for _ in ()).throw(RepeatedInitializationError()))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Lifecycle ────────────────────────────────────────────────────────────")

check("NotInitializedError: target in message",
      NotInitializedError,
      lambda: (_ for _ in ()).throw(NotInitializedError(target="DatabaseConnection")),
      attr_checks={"target": "DatabaseConnection"})

check("AlreadyDisposedError: target attr",
      AlreadyDisposedError,
      lambda: (_ for _ in ()).throw(AlreadyDisposedError(target="Socket")),
      attr_checks={"target": "Socket"})

check("TeardownError: target+reason",
      TeardownError,
      lambda: (_ for _ in ()).throw(TeardownError(target="Pipeline", reason="file lock")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Options ──────────────────────────────────────────────────────────────")

check("MissingOptionError: option attr",
      MissingOptionError,
      lambda: (_ for _ in ()).throw(MissingOptionError(option="API_KEY")),
      attr_checks={"option": "API_KEY"})

check("OptionConflictError: both options in attrs",
      OptionConflictError,
      lambda: (_ for _ in ()).throw(OptionConflictError(option_a="verbose", option_b="quiet")),
      attr_checks={"option_a": "verbose", "option_b": "quiet"})

check("OptionReadOnlyError",
      OptionReadOnlyError,
      lambda: (_ for _ in ()).throw(OptionReadOnlyError(option="theme")))

check("InvalidOptionValueError",
      InvalidOptionValueError,
      lambda: (_ for _ in ()).throw(InvalidOptionValueError(option="mode", value="???")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Architecture ─────────────────────────────────────────────────────────")

check("AbstractMethodNotImplementedError",
      AbstractMethodNotImplementedError,
      lambda: (_ for _ in ()).throw(AbstractMethodNotImplementedError(method="process")))

check("InterfaceContractError",
      InterfaceContractError,
      lambda: (_ for _ in ()).throw(InterfaceContractError(interface="IRepo", detail="missing find")))

check("CircularDependencyError",
      CircularDependencyError,
      lambda: (_ for _ in ()).throw(CircularDependencyError(cycle=["A", "B", "A"])))

check("ComponentNotRegisteredError",
      ComponentNotRegisteredError,
      lambda: (_ for _ in ()).throw(ComponentNotRegisteredError(component="AuthService")))

check("ComponentAlreadyRegisteredError",
      ComponentAlreadyRegisteredError,
      lambda: (_ for _ in ()).throw(ComponentAlreadyRegisteredError(component="LogService")))

check("LayerViolationError",
      LayerViolationError,
      lambda: (_ for _ in ()).throw(LayerViolationError(from_layer="domain", to_layer="infra")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Flow Control ─────────────────────────────────────────────────────────")

check("ConditionNotMetError",
      ConditionNotMetError,
      lambda: (_ for _ in ()).throw(ConditionNotMetError(condition="user_logged_in")))

check("ExecutionOrderError",
      ExecutionOrderError,
      lambda: (_ for _ in ()).throw(ExecutionOrderError(step="load", expected_before="connect")))

check("FlowInterruptedError",
      FlowInterruptedError,
      lambda: (_ for _ in ()).throw(FlowInterruptedError(stage="transform")))

check("PipelineCancelledError",
      PipelineCancelledError,
      lambda: (_ for _ in ()).throw(PipelineCancelledError(pipeline="etl_main")))

check("StepAbortedError",
      StepAbortedError,
      lambda: (_ for _ in ()).throw(StepAbortedError(step="validate", reason="null data")))

check("MaxIterationsExceededError",
      MaxIterationsExceededError,
      lambda: (_ for _ in ()).throw(MaxIterationsExceededError(max_iterations=100)))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Validation ───────────────────────────────────────────────────────────")

check("ConfigurationError",
      ConfigurationError,
      lambda: (_ for _ in ()).throw(ConfigurationError(key="DB_URL")))

check("ValidationError",
      ValidationError,
      lambda: (_ for _ in ()).throw(ValidationError(field="email", reason="invalid format")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Runtime ──────────────────────────────────────────────────────────────")

check("TimeoutExpiredError",
      TimeoutExpiredError,
      lambda: (_ for _ in ()).throw(TimeoutExpiredError(operation="fetch_api", seconds=30)))

check("DependencyError",
      DependencyError,
      lambda: (_ for _ in ()).throw(DependencyError(dependency="openpyxl")))

check("ReadOnlyError",
      ReadOnlyError,
      lambda: (_ for _ in ()).throw(ReadOnlyError(target="config")))

check("StateError",
      StateError,
      lambda: (_ for _ in ()).throw(StateError(current_state="stopped", expected_state="running")))

check("FeatureNotSupportedError",
      FeatureNotSupportedError,
      lambda: (_ for _ in ()).throw(FeatureNotSupportedError(feature="GPU")))

check("ResourceExhaustedError",
      ResourceExhaustedError,
      lambda: (_ for _ in ()).throw(ResourceExhaustedError(resource="connection_pool")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── ETL ──────────────────────────────────────────────────────────────────")

check("DataExtractionError",
      DataExtractionError,
      lambda: (_ for _ in ()).throw(DataExtractionError(source="s3://bucket", reason="timeout")))

check("DataTransformationError",
      DataTransformationError,
      lambda: (_ for _ in ()).throw(DataTransformationError(step="normalize", reason="null col")))

check("DataLoadError",
      DataLoadError,
      lambda: (_ for _ in ()).throw(DataLoadError(target="postgres", reason="auth failed")))

check("SchemaValidationError",
      SchemaValidationError,
      lambda: (_ for _ in ()).throw(SchemaValidationError(detail="missing 'id' column")))

check("MissingColumnError",
      MissingColumnError,
      lambda: (_ for _ in ()).throw(MissingColumnError(column="user_id", dataset="users.csv")))

check("DataTypeConversionError",
      DataTypeConversionError,
      lambda: (_ for _ in ()).throw(DataTypeConversionError(value="age", target_type="int")))

check("DuplicateRecordError",
      DuplicateRecordError,
      lambda: (_ for _ in ()).throw(DuplicateRecordError(key="txn_123")))

check("EmptyDatasetError",
      EmptyDatasetError,
      lambda: (_ for _ in ()).throw(EmptyDatasetError(source="daily_batch")))

check("DataCorruptionError",
      DataCorruptionError,
      lambda: (_ for _ in ()).throw(DataCorruptionError(source="archive.parquet", reason="bad checksum")))

check("PartitionError",
      PartitionError,
      lambda: (_ for _ in ()).throw(PartitionError(detail="partition 2024-01 overlap")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── GUI ──────────────────────────────────────────────────────────────────")

check("WidgetNotFoundError",
      WidgetNotFoundError,
      lambda: (_ for _ in ()).throw(WidgetNotFoundError(widget_id="btn_submit")))

check("UIStateError",
      UIStateError,
      lambda: (_ for _ in ()).throw(UIStateError(current_state="closed")))

check("RenderError",
      RenderError,
      lambda: (_ for _ in ()).throw(RenderError(component="Canvas", reason="null context")))

check("EventHandlerError",
      EventHandlerError,
      lambda: (_ for _ in ()).throw(EventHandlerError(event="on_click", reason="NullRef")))

check("LayoutError",
      LayoutError,
      lambda: (_ for _ in ()).throw(LayoutError(detail="GridPanel: divide by zero")))

check("ThemeNotFoundError",
      ThemeNotFoundError,
      lambda: (_ for _ in ()).throw(ThemeNotFoundError(theme="nord")))

check("WindowNotOpenError",
      WindowNotOpenError,
      lambda: (_ for _ in ()).throw(WindowNotOpenError(window="settings_dialog")))

check("ScreenResolutionError",
      ScreenResolutionError,
      lambda: (_ for _ in ()).throw(ScreenResolutionError(required="1920x1080", actual="800x600")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Monitoring ───────────────────────────────────────────────────────────")

check("MetricCollectionError",
      MetricCollectionError,
      lambda: (_ for _ in ()).throw(MetricCollectionError(metric="cpu_usage", reason="agent dead")))

check("ThresholdExceededError",
      ThresholdExceededError,
      lambda: (_ for _ in ()).throw(ThresholdExceededError(metric="latency", threshold=200, value=350)))

check("WatchdogTriggeredError",
      WatchdogTriggeredError,
      lambda: (_ for _ in ()).throw(WatchdogTriggeredError(target="heartbeat_worker")))

check("HealthCheckFailedError",
      HealthCheckFailedError,
      lambda: (_ for _ in ()).throw(HealthCheckFailedError(component="redis", reason="timeout")))

check("ProbeTimeoutError",
      ProbeTimeoutError,
      lambda: (_ for _ in ()).throw(ProbeTimeoutError(probe="liveness", timeout_s=5)))

check("ObservabilityError",
      ObservabilityError,
      lambda: (_ for _ in ()).throw(ObservabilityError(backend="otel_exporter", reason="conn refused")))

check("SamplingError",
      SamplingError,
      lambda: (_ for _ in ()).throw(SamplingError(source="request_rate", reason="buffer overflow")))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── AI Training ──────────────────────────────────────────────────────────")

check("ModelNotFittedError",
      ModelNotFittedError,
      lambda: (_ for _ in ()).throw(ModelNotFittedError(model="LinearRegressor")))

check("CheckpointNotFoundError",
      CheckpointNotFoundError,
      lambda: (_ for _ in ()).throw(CheckpointNotFoundError(path="./ckpt/epoch_10.pt")))

check("TrainingInterruptedError",
      TrainingInterruptedError,
      lambda: (_ for _ in ()).throw(TrainingInterruptedError(epoch=7, reason="OOM")))

check("HyperparameterError",
      HyperparameterError,
      lambda: (_ for _ in ()).throw(HyperparameterError(param="lr", value=-0.1)))

check("DatasetSplitError",
      DatasetSplitError,
      lambda: (_ for _ in ()).throw(DatasetSplitError(reason="train+val+test != 1.0")))

check("GradientExplosionError",
      GradientExplosionError,
      lambda: (_ for _ in ()).throw(GradientExplosionError(layer="fc1", norm=1e8)))

check("GradientVanishingError",
      GradientVanishingError,
      lambda: (_ for _ in ()).throw(GradientVanishingError(layer="lstm_0", norm=1e-12)))

check("InferenceError",
      InferenceError,
      lambda: (_ for _ in ()).throw(InferenceError(model="BERT", reason="input too long")))

check("EpochLimitReachedError",
      EpochLimitReachedError,
      lambda: (_ for _ in ()).throw(EpochLimitReachedError(max_epochs=100)))

check("ModelArchitectureError",
      ModelArchitectureError,
      lambda: (_ for _ in ()).throw(ModelArchitectureError(detail="output dim mismatch")))

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  結果：{PASS} PASS  /  {FAIL} FAIL")
if FAIL:
    print("  ⚠  有測試失敗，請檢查上方輸出。")
else:
    print("  🎉 全部通過！")
print("=" * 60)
