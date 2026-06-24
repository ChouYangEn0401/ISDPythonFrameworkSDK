"""
ISD Python Framework — Public API.

The flat public API is **lazily loaded** (PEP 562). ``import isd_py_framework_sdk``
imports almost nothing; each name — and each feature subpackage — is resolved on
first access and then cached. This keeps startup cheap and, crucially, means the
optional heavy backends (``pandas``, ``openpyxl``, ``colorama``, ``cryptography``
…) are **never** pulled in until you actually touch a feature that needs them::

    import isd_py_framework_sdk as isd

    isd.SingletonMetaclass   # resolved from base on first use
    isd.retry                # resolved from helpers.decorators on first use
    isd.cipher_kit           # the subpackage, imported on first access

Both styles keep working unchanged::

    from isd_py_framework_sdk import retry, SingletonSystemLogger
    from isd_py_framework_sdk.cipher_kit import seal, unseal

Adding a public name: list it under the right module in ``_FLAT_EXPORTS`` (and,
for editor autocomplete, in the ``TYPE_CHECKING`` block below).
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from ._version import __version__

# ── Flat re-exports: source module (relative) → the names it provides ────────
# This is the single source of truth that drives lazy resolution. Names are
# imported from their module only on first access.
_FLAT_EXPORTS: dict[str, tuple[str, ...]] = {
    ".base.Singleton": (
        "SingletonMetaclass",
    ),
    ".events": (
        "IEventBase", "IParsEventBase", "SingletonEventManager", "IDelayEventBase",
        "IDelayParsEventBase", "DelayEventBusManager", "MulticastCallback",
    ),
    ".message_logger": (
        "SingletonSystemLogger", "get_logger", "configure_logger", "LoggerAdapterBase",
        "DarkThemeTerminalAdapter", "LightThemeTerminalAdapter", "FileAdapter", "DarkThemeTkinterAdapter",
        "LightThemeTkinterAdapter", "DarkThemeTkLabelAdapter", "LightThemeTkLabelAdapter", "DarkThemeTtkLabelAdapter",
        "LightThemeTtkLabelAdapter", "LocalHTTPAdapter", "QueuedSocketAdapter", "AbstractTkinterAdapterBase",
    ),
    ".helpers.decorators": (
        "function_timer", "timed_and_conditional_return", "test_func", "old_method",
        "deprecated", "battered", "log_call", "count_calls",
        "profile_memory", "experimental", "removed_in", "since",
        "retry", "once", "suppress_exceptions", "throttle",
        "timeout", "run_in_thread", "synchronized", "etl_step",
        "log_record_count", "checkpoint", "skip_on_empty", "idempotent_load",
        "not_none", "validate_args", "validate_return", "ensure_type",
        "clamp_return", "non_empty_return", "require_main_thread", "debounce",
        "gui_error_handler", "disable_widget_during_run", "run_after", "emit_metric",
        "watchdog_ping", "health_check", "alert_on_failure", "rate_limit",
        "training_step", "log_epoch", "inference_only", "cache_predictions",
        "grad_check", "single_responsibility", "layer", "interface_method",
        "abstract_implementation", "no_side_effects", "sealed", "require_override",
        "enforce_srp",
    ),
    ".helpers.exceptions": (
        "WrongOptionException", "WrongImplementationException", "UnhandledConditionError", "RepeatedInitializationError",
        "NotInitializedError", "AlreadyDisposedError", "TeardownError", "MissingOptionError",
        "OptionConflictError", "OptionReadOnlyError", "InvalidOptionValueError", "AbstractMethodNotImplementedError",
        "InterfaceContractError", "CircularDependencyError", "ComponentNotRegisteredError", "ComponentAlreadyRegisteredError",
        "LayerViolationError", "ConditionNotMetError", "ExecutionOrderError", "FlowInterruptedError",
        "PipelineCancelledError", "StepAbortedError", "MaxIterationsExceededError", "ConfigurationError",
        "ValidationError", "TimeoutExpiredError", "DependencyError", "ReadOnlyError",
        "StateError", "FeatureNotSupportedError", "ResourceExhaustedError", "DataExtractionError",
        "DataTransformationError", "DataLoadError", "SchemaValidationError", "MissingColumnError",
        "DataTypeConversionError", "DuplicateRecordError", "EmptyDatasetError", "DataCorruptionError",
        "PartitionError", "WidgetNotFoundError", "UIStateError", "RenderError",
        "EventHandlerError", "LayoutError", "ThemeNotFoundError", "WindowNotOpenError",
        "ScreenResolutionError", "MetricCollectionError", "ThresholdExceededError", "WatchdogTriggeredError",
        "HealthCheckFailedError", "ProbeTimeoutError", "ObservabilityError", "SamplingError",
        "ModelNotFittedError", "CheckpointNotFoundError", "TrainingInterruptedError", "HyperparameterError",
        "DatasetSplitError", "GradientExplosionError", "GradientVanishingError", "InferenceError",
        "EpochLimitReachedError", "ModelArchitectureError",
    ),
    ".helpers.assertions": (
        "assert__is_str", "assert__is_list_of_str", "assert__is_list_of_list_of_str", "assert__is_list_of_tuple_of_str",
        "assert__is_int", "assert__is_float", "assert__is_number", "assert__is_bool",
        "assert__is_dict", "assert__is_list", "assert__is_tuple", "assert__is_set",
        "assert__is_callable", "assert__is_none", "assert__is_not_none", "assert__is_instance",
        "assert__is_subclass", "assert__is_list_of_int", "assert__is_list_of_float", "assert__is_list_of_number",
        "assert__is_dict_of_str_to_str", "assert__is_positive", "assert__is_non_negative", "assert__is_not_empty",
        "assert__in_range", "assert__is_one_of", "assert__matches_pattern", "assert__has_length",
        "assert__min_length", "assert__max_length", "assert__all_keys_exist", "assert__is_unique",
        "assert__no_none_values", "assert__contains_in_list", "assert__contains_in_str", "assert__contains_in_dataclass",
        "assert__contains_in_object",
    ),
}

# ── Feature subpackages + backward-compatible short-path shims ───────────────
# Accessible as attributes (``isd.cipher_kit``) and imported lazily on first
# access. Deliberately NOT in ``__all__`` so ``from isd_py_framework_sdk import *``
# never drags a heavy subpackage in.
_LAZY_SUBMODULES: frozenset[str] = frozenset({
    "base", "events", "message_logger", "monitoring", "file_compare",
    "path_manager", "unified_io", "excel_painter", "cipher_kit",
    "credential_vault", "helpers", "window_design_helper",
    # short-path shims (re-export only; kept for backward compatibility)
    "interface", "events_bus", "msg_logger", "assertions", "decorators", "exceptions",
})

# name → relative module, built once (no imports happen here)
_NAME_TO_MODULE: dict[str, str] = {
    name: module for module, names in _FLAT_EXPORTS.items() for name in names
}

# ``AbstractTkinterAdapterBase`` stays importable but, as before, is not in
# ``__all__`` (it is an advanced base class, not part of the common surface).
__all__ = ["__version__"] + [
    name for name in _NAME_TO_MODULE if name != "AbstractTkinterAdapterBase"
]


def __getattr__(name: str):
    """PEP 562 lazy attribute resolution for the flat API and subpackages."""
    module_path = _NAME_TO_MODULE.get(name)
    if module_path is not None:
        module = importlib.import_module(module_path, __name__)
        value = getattr(module, name)
        globals()[name] = value  # cache: subsequent access skips __getattr__
        return value
    if name in _LAZY_SUBMODULES:
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*__all__, *_LAZY_SUBMODULES, "AbstractTkinterAdapterBase"])


if TYPE_CHECKING:  # static-analysis only — gives editors/type-checkers the flat API
    from .base.Singleton import SingletonMetaclass as SingletonMetaclass
    from .events import (
        IEventBase as IEventBase,
        IParsEventBase as IParsEventBase,
        SingletonEventManager as SingletonEventManager,
        IDelayEventBase as IDelayEventBase,
        IDelayParsEventBase as IDelayParsEventBase,
        DelayEventBusManager as DelayEventBusManager,
        MulticastCallback as MulticastCallback,
    )
    from .message_logger import (
        SingletonSystemLogger as SingletonSystemLogger,
        get_logger as get_logger,
        configure_logger as configure_logger,
        LoggerAdapterBase as LoggerAdapterBase,
        DarkThemeTerminalAdapter as DarkThemeTerminalAdapter,
        LightThemeTerminalAdapter as LightThemeTerminalAdapter,
        FileAdapter as FileAdapter,
        AbstractTkinterAdapterBase as AbstractTkinterAdapterBase,
        DarkThemeTkinterAdapter as DarkThemeTkinterAdapter,
        LightThemeTkinterAdapter as LightThemeTkinterAdapter,
        DarkThemeTkLabelAdapter as DarkThemeTkLabelAdapter,
        LightThemeTkLabelAdapter as LightThemeTkLabelAdapter,
        DarkThemeTtkLabelAdapter as DarkThemeTtkLabelAdapter,
        LightThemeTtkLabelAdapter as LightThemeTtkLabelAdapter,
        LocalHTTPAdapter as LocalHTTPAdapter,
        QueuedSocketAdapter as QueuedSocketAdapter,
    )
    from .helpers.decorators import *  # noqa: F401,F403
    from .helpers.exceptions import *  # noqa: F401,F403
    from .helpers.assertions import *  # noqa: F401,F403
