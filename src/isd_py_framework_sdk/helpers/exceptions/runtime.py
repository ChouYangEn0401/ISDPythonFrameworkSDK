"""
Runtime exceptions — errors that occur during program execution.
"""


class TimeoutExpiredError(Exception):
    """Raised when an operation exceeds the allowed time limit."""

    def __init__(self, operation: str = "", seconds: float | None = None, message: str | None = None):
        if message is None:
            parts = ["Operation timed out"]
            if operation:
                parts = [f"Operation '{operation}' timed out"]
            if seconds is not None:
                parts.append(f"after {seconds:.1f}s")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.operation = operation
        self.seconds = seconds


class DependencyError(Exception):
    """Raised when a required external dependency (package/module/service) is missing or incompatible."""

    def __init__(self, dependency: str = "", message: str | None = None):
        if message is None:
            if dependency:
                message = f"Required dependency '{dependency}' is missing or incompatible."
            else:
                message = "A required dependency is missing."
        super().__init__(message)
        self.dependency = dependency


class ReadOnlyError(Exception):
    """Raised when attempting to modify a resource that is read-only or frozen."""

    def __init__(self, target: str = "", message: str | None = None):
        if message is None:
            if target:
                message = f"'{target}' is read-only and cannot be modified."
            else:
                message = "This resource is read-only."
        super().__init__(message)
        self.target = target


class StateError(Exception):
    """Raised when an object is in an invalid state for the requested operation."""

    def __init__(self, current_state: str = "", expected_state: str = "", message: str | None = None):
        if message is None:
            parts = ["Invalid state for this operation"]
            if current_state:
                detail = f"(current: '{current_state}'"
                if expected_state:
                    detail += f", expected: '{expected_state}'"
                detail += ")"
                parts.append(detail)
            message = " ".join(parts) + "."
        super().__init__(message)
        self.current_state = current_state
        self.expected_state = expected_state


class FeatureNotSupportedError(Exception):
    """Raised when a requested feature or operation is not available in the current context."""

    def __init__(self, feature: str = "", message: str | None = None):
        if message is None:
            if feature:
                message = f"Feature '{feature}' is not supported."
            else:
                message = "This feature is not supported."
        super().__init__(message)
        self.feature = feature


class ResourceExhaustedError(Exception):
    """Raised when a resource pool, quota, or capacity limit has been reached."""

    def __init__(self, resource: str = "", message: str | None = None):
        if message is None:
            if resource:
                message = f"Resource '{resource}' has been exhausted."
            else:
                message = "Resource limit has been reached."
        super().__init__(message)
        self.resource = resource
