"""
isd_py_framework_sdk.helpers.exceptions — All custom exception classes.
"""


# ── Lifecycle ─────────────────────────────────────────────────────────────
from .lifecycle import (
    NotInitializedError,
    RepeatedInitializationError,
    AlreadyDisposedError,
    TeardownError,
)

# ── Options / interface management ───────────────────────────────────────
from .options import (
    WrongOptionException,
    MissingOptionError,
    OptionConflictError,
    OptionReadOnlyError,
    InvalidOptionValueError,
)

# ── Architecture / design contracts ──────────────────────────────────────
from .architecture import (
    WrongImplementationException,
    AbstractMethodNotImplementedError,
    InterfaceContractError,
    CircularDependencyError,
    ComponentNotRegisteredError,
    ComponentAlreadyRegisteredError,
    LayerViolationError,
)

# ── Flow control ─────────────────────────────────────────────────────────
from .flow_control import (
    UnhandledConditionError,
    ConditionNotMetError,
    ExecutionOrderError,
    FlowInterruptedError,
    PipelineCancelledError,
    StepAbortedError,
    MaxIterationsExceededError,
)

# ── Validation ────────────────────────────────────────────────────────────
from .validation import (
    ConfigurationError,
    ValidationError,
)

# ── Runtime ───────────────────────────────────────────────────────────────
from .runtime import (
    TimeoutExpiredError,
    DependencyError,
    ReadOnlyError,
    StateError,
    FeatureNotSupportedError,
    ResourceExhaustedError,
)

# ── ETL ───────────────────────────────────────────────────────────────────
from .etl import (
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
)

# ── GUI ───────────────────────────────────────────────────────────────────
from .gui import (
    WidgetNotFoundError,
    UIStateError,
    RenderError,
    EventHandlerError,
    LayoutError,
    ThemeNotFoundError,
    WindowNotOpenError,
    ScreenResolutionError,
)

# ── Monitoring ────────────────────────────────────────────────────────────
from .monitoring import (
    MetricCollectionError,
    ThresholdExceededError,
    WatchdogTriggeredError,
    HealthCheckFailedError,
    ProbeTimeoutError,
    ObservabilityError,
    SamplingError,
)

# ── AI / ML training ─────────────────────────────────────────────────────
from .ai_training import (
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

__all__ = [
    # ── legacy shim ──────────────────────────────────────────────────────
    "WrongOptionException",
    "WrongImplementationException",
    "UnhandledConditionError",
    "RepeatedInitializationError",
    # ── lifecycle ────────────────────────────────────────────────────────
    "NotInitializedError",
    "AlreadyDisposedError",
    "TeardownError",
    # ── options ──────────────────────────────────────────────────────────
    "MissingOptionError",
    "OptionConflictError",
    "OptionReadOnlyError",
    "InvalidOptionValueError",
    # ── architecture ─────────────────────────────────────────────────────
    "AbstractMethodNotImplementedError",
    "InterfaceContractError",
    "CircularDependencyError",
    "ComponentNotRegisteredError",
    "ComponentAlreadyRegisteredError",
    "LayerViolationError",
    # ── flow control ─────────────────────────────────────────────────────
    "ConditionNotMetError",
    "ExecutionOrderError",
    "FlowInterruptedError",
    "PipelineCancelledError",
    "StepAbortedError",
    "MaxIterationsExceededError",
    # ── validation ───────────────────────────────────────────────────────
    "ConfigurationError",
    "ValidationError",
    # ── runtime ──────────────────────────────────────────────────────────
    "TimeoutExpiredError",
    "DependencyError",
    "ReadOnlyError",
    "StateError",
    "FeatureNotSupportedError",
    "ResourceExhaustedError",
    # ── ETL ──────────────────────────────────────────────────────────────
    "DataExtractionError",
    "DataTransformationError",
    "DataLoadError",
    "SchemaValidationError",
    "MissingColumnError",
    "DataTypeConversionError",
    "DuplicateRecordError",
    "EmptyDatasetError",
    "DataCorruptionError",
    "PartitionError",
    # ── GUI ──────────────────────────────────────────────────────────────
    "WidgetNotFoundError",
    "UIStateError",
    "RenderError",
    "EventHandlerError",
    "LayoutError",
    "ThemeNotFoundError",
    "WindowNotOpenError",
    "ScreenResolutionError",
    # ── monitoring ───────────────────────────────────────────────────────
    "MetricCollectionError",
    "ThresholdExceededError",
    "WatchdogTriggeredError",
    "HealthCheckFailedError",
    "ProbeTimeoutError",
    "ObservabilityError",
    "SamplingError",
    # ── AI / ML training ─────────────────────────────────────────────────
    "ModelNotFittedError",
    "CheckpointNotFoundError",
    "TrainingInterruptedError",
    "HyperparameterError",
    "DatasetSplitError",
    "GradientExplosionError",
    "GradientVanishingError",
    "InferenceError",
    "EpochLimitReachedError",
    "ModelArchitectureError",
]

