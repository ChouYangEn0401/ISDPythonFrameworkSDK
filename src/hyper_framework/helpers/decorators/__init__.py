"""
hyper_framework.helpers.decorators — All decorator utilities.

Modules:
  decorators_pack  — Legacy shim (backward-compat re-exports)
  profiling        — Timing, call counting, memory profiling
  lifecycle        — API lifecycle / versioning signals
  control_flow     — Retry, throttle, once, suppress, timeout
  concurrency      — Thread / lock helpers
  etl              — ETL pipeline step decoration
  validation       — Input / output boundary guards
  gui              — GUI thread-safety, debounce, widget helpers
  monitoring       — Metrics, watchdog, health checks, rate limiting
  ai_training      — ML training / inference lifecycle
  architecture     — SRP enforcement, layer guards, interface contracts
"""

# ── Profiling (timing, call counting, memory) ─────────────────────────────
from .profiling import (
    log_call,
    count_calls,
    profile_memory,
    function_timer,
    timed_and_conditional_return,
)

# ── Lifecycle (API versioning signals) ───────────────────────────────────
from .lifecycle import (
    deprecated,
    battered,
    experimental,
    removed_in,
    since,
)

# ── Control-flow ──────────────────────────────────────────────────────────
from .control_flow import (
    retry,
    once,
    suppress_exceptions,
    throttle,
    timeout,
)

# ── Concurrency ──────────────────────────────────────────────────────────
from .concurrency import (
    run_in_thread,
    synchronized,
)

# ── ETL — pipeline step decoration ───────────────────────────────────────
from .etl import (
    etl_step,
    log_record_count,
    checkpoint,
    skip_on_empty,
    idempotent_load,
)

# ── Validation — boundary guards ─────────────────────────────────────────
from .validation import (
    not_none,
    validate_args,
    validate_return,
    ensure_type,
    clamp_return,
    non_empty_return,
)

# ── GUI — thread-safety & widget helpers ─────────────────────────────────
from .gui import (
    require_main_thread,
    debounce,
    gui_error_handler,
    disable_widget_during_run,
    run_after,
)

# ── Monitoring — metrics, watchdog, health checks ────────────────────────
from .monitoring import (
    emit_metric,
    watchdog_ping,
    health_check,
    alert_on_failure,
    rate_limit,
)

# ── AI / ML training — lifecycle decoration ──────────────────────────────
from .ai_training import (
    training_step,
    log_epoch,
    inference_only,
    cache_predictions,
    grad_check,
)

# ── Architecture — SRP, layers, interface contracts ───────────────────────
from .architecture import (
    single_responsibility,
    layer,
    interface_method,
    abstract_implementation,
    no_side_effects,
    sealed,
    require_override,
    enforce_srp,
)

__all__ = [
    # legacy / profiling
    "function_timer",
    "timed_and_conditional_return",
    "deprecated",
    "battered",
    # profiling (new)
    "log_call",
    "count_calls",
    "profile_memory",
    # lifecycle (new)
    "experimental",
    "removed_in",
    "since",
    # control-flow
    "retry",
    "once",
    "suppress_exceptions",
    "throttle",
    "timeout",
    # concurrency
    "run_in_thread",
    "synchronized",
    # ETL
    "etl_step",
    "log_record_count",
    "checkpoint",
    "skip_on_empty",
    "idempotent_load",
    # validation
    "not_none",
    "validate_args",
    "validate_return",
    "ensure_type",
    "clamp_return",
    "non_empty_return",
    # GUI
    "require_main_thread",
    "debounce",
    "gui_error_handler",
    "disable_widget_during_run",
    "run_after",
    # monitoring
    "emit_metric",
    "watchdog_ping",
    "health_check",
    "alert_on_failure",
    "rate_limit",
    # AI / ML training
    "training_step",
    "log_epoch",
    "inference_only",
    "cache_predictions",
    "grad_check",
    # architecture / SRP
    "single_responsibility",
    "layer",
    "interface_method",
    "abstract_implementation",
    "no_side_effects",
    "sealed",
    "require_override",
    "enforce_srp",
]
