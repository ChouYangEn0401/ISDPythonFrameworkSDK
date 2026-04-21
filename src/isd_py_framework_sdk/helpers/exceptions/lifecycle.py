"""
Lifecycle exceptions — errors related to object initialization, teardown, and lifecycle management.

Migrated from exceptions.py:
  - RepeatedInitializationError
"""


class NotInitializedError(Exception):
    """Raised when an object is accessed or used before it has been initialized."""

    def __init__(self, target: str = "", message: str | None = None):
        if message is None:
            if target:
                message = f"'{target}' has not been initialized yet. Call the initialization method first."
            else:
                message = "Object has not been initialized yet."
        super().__init__(message)
        self.target = target


class RepeatedInitializationError(Exception):
    """Raised when an object is initialized or registered more than once."""

    def __init__(self, target: str = "", message: str | None = None):
        if message is None:
            if target:
                message = f"'{target}' has already been initialized and cannot be initialized again."
            else:
                message = "This object has already been initialized and cannot be initialized again."
        super().__init__(message)
        self.target = target


class AlreadyDisposedError(Exception):
    """Raised when an operation is attempted on an object that has already been disposed/closed."""

    def __init__(self, target: str = "", message: str | None = None):
        if message is None:
            if target:
                message = f"'{target}' has already been disposed and can no longer be used."
            else:
                message = "This object has already been disposed."
        super().__init__(message)
        self.target = target


class TeardownError(Exception):
    """Raised when an error occurs during the teardown/cleanup phase of an object or system."""

    def __init__(self, target: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Teardown failed"]
            if target:
                parts = [f"Teardown of '{target}' failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.target = target
        self.reason = reason
