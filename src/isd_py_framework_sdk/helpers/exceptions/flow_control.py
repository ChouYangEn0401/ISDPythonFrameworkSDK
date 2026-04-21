"""
Flow-control exceptions — errors that arise in conditional branching, pipeline
step sequencing, and process orchestration.

Migrated from exceptions.py:
  - UnhandledConditionError
"""


class UnhandledConditionError(Exception):
    """
    Raised when an if-elif-else tree does not cover the encountered case.

    Pass any relevant variables as keyword arguments — they will be included
    in the error message automatically.

    e.g.::

        raise UnhandledConditionError(mode=mode, value=value)
    """

    def __init__(self, message: str | None = None, **kwargs):
        if message is None:
            details = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            if details:
                message = f"程式條件判斷未涵蓋此狀態！未處理的詳細資訊: {details}"
            else:
                message = "程式條件判斷未涵蓋此狀態！"
        super().__init__(message)
        self.details = kwargs


class ConditionNotMetError(Exception):
    """Raised when a required pre-condition or guard condition is not satisfied."""

    def __init__(self, condition: str = "", message: str | None = None):
        if message is None:
            if condition:
                message = f"Required condition not met: '{condition}'."
            else:
                message = "A required condition was not met."
        super().__init__(message)
        self.condition = condition


class ExecutionOrderError(Exception):
    """Raised when a step or method is invoked out of the expected execution order."""

    def __init__(self, step: str = "", expected_before: str = "", message: str | None = None):
        if message is None:
            if step and expected_before:
                message = f"Step '{step}' must be called after '{expected_before}'."
            elif step:
                message = f"Step '{step}' was invoked out of order."
            else:
                message = "A step was invoked out of the expected execution order."
        super().__init__(message)
        self.step = step
        self.expected_before = expected_before


class FlowInterruptedError(Exception):
    """Raised when the normal execution flow is interrupted unexpectedly (not by user cancellation)."""

    def __init__(self, stage: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = ["Execution flow was unexpectedly interrupted"]
            if stage:
                parts = [f"Execution flow was unexpectedly interrupted at stage '{stage}'"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.stage = stage
        self.reason = reason


class PipelineCancelledError(Exception):
    """Raised when a pipeline or workflow is intentionally cancelled (e.g. by user request or signal)."""

    def __init__(self, pipeline: str = "", message: str | None = None):
        if message is None:
            if pipeline:
                message = f"Pipeline '{pipeline}' was cancelled before completion."
            else:
                message = "The pipeline was cancelled before completion."
        super().__init__(message)
        self.pipeline = pipeline


class StepAbortedError(Exception):
    """Raised when a single pipeline step is aborted and the pipeline should stop."""

    def __init__(self, step: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = ["Step was aborted"]
            if step:
                parts = [f"Step '{step}' was aborted"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.step = step
        self.reason = reason


class MaxIterationsExceededError(Exception):
    """Raised when a loop or iterative algorithm exceeds its allowed iteration count."""

    def __init__(self, max_iterations: int | None = None, message: str | None = None):
        if message is None:
            if max_iterations is not None:
                message = f"Maximum iteration limit of {max_iterations} was exceeded."
            else:
                message = "Maximum iteration limit was exceeded."
        super().__init__(message)
        self.max_iterations = max_iterations
