"""
Validation exceptions — errors related to configuration and data validation.
"""


class ConfigurationError(Exception):
    """Raised when a configuration value is missing, invalid, or incompatible."""

    def __init__(self, key: str = "", message: str | None = None):
        if message is None:
            if key:
                message = f"Configuration error for key '{key}'."
            else:
                message = "Invalid or missing configuration."
        super().__init__(message)
        self.key = key


class ValidationError(Exception):
    """Raised when input data fails a validation check."""

    def __init__(self, field: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = ["Validation failed"]
            if field:
                parts.append(f"for field '{field}'")
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.field = field
        self.reason = reason
