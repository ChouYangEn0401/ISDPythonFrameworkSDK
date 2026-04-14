"""
Monitoring / observability exceptions — errors related to system-health checks,
metric collection, alerting thresholds, and watchdog supervision.
"""


class MetricCollectionError(Exception):
    """Raised when a metric cannot be collected from its source."""

    def __init__(self, metric: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Failed to collect metric '{metric}'"] if metric else ["Metric collection failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.metric = metric
        self.reason = reason


class ThresholdExceededError(Exception):
    """Raised when a monitored value crosses a defined alert threshold."""

    def __init__(
        self,
        metric: str = "",
        value=None,
        threshold=None,
        message: str | None = None,
    ):
        if message is None:
            if metric and value is not None and threshold is not None:
                message = (
                    f"Metric '{metric}' exceeded threshold: "
                    f"value={value!r}, threshold={threshold!r}."
                )
            elif metric:
                message = f"Metric '{metric}' exceeded its defined threshold."
            else:
                message = "A monitored metric exceeded its threshold."
        super().__init__(message)
        self.metric = metric
        self.value = value
        self.threshold = threshold


class WatchdogTriggeredError(Exception):
    """Raised when a watchdog timer or supervisor detects that a process is unresponsive."""

    def __init__(self, target: str = "", timeout_s: float | None = None, message: str | None = None):
        if message is None:
            if target and timeout_s is not None:
                message = f"Watchdog triggered: '{target}' was unresponsive for {timeout_s:.1f}s."
            elif target:
                message = f"Watchdog triggered: '{target}' is unresponsive."
            else:
                message = "Watchdog triggered: a monitored process is unresponsive."
        super().__init__(message)
        self.target = target
        self.timeout_s = timeout_s


class HealthCheckFailedError(Exception):
    """Raised when a health-check probe determines that a service or component is unhealthy."""

    def __init__(self, component: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Health check failed for '{component}'"] if component else ["Health check failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.component = component
        self.reason = reason


class ProbeTimeoutError(Exception):
    """Raised when a readiness or liveness probe does not respond within the allowed window."""

    def __init__(self, probe: str = "", timeout_s: float | None = None, message: str | None = None):
        if message is None:
            if probe and timeout_s is not None:
                message = f"Probe '{probe}' timed out after {timeout_s:.1f}s."
            elif probe:
                message = f"Probe '{probe}' timed out."
            else:
                message = "A readiness/liveness probe timed out."
        super().__init__(message)
        self.probe = probe
        self.timeout_s = timeout_s


class ObservabilityError(Exception):
    """General error for observability infrastructure failures (tracing, logging sinks, exporters)."""

    def __init__(self, backend: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Observability backend '{backend}' error"] if backend else ["Observability error"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.backend = backend
        self.reason = reason


class SamplingError(Exception):
    """Raised when a telemetry or data-sampling operation fails or yields invalid samples."""

    def __init__(self, source: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Sampling from '{source}' failed"] if source else ["Sampling failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.source = source
        self.reason = reason
