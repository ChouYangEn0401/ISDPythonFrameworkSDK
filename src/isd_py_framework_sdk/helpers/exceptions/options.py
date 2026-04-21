"""
Options / interface-management exceptions — errors related to option choices,
flags, and configuration interface contracts.

Migrated from exceptions.py:
  - WrongOptionException
"""


class WrongOptionException(Exception):
    """
    Raised when an unrecognised or unsupported option/mode value is provided.

    e.g.::

        raise WrongOptionException(option="mode_x")
    """

    def __init__(self, option, message: str | None = None):
        if message is None:
            message = f"No Mode Found !! Wrong：`{option}` !!"
        super().__init__(message)
        self.option = option


class MissingOptionError(Exception):
    """Raised when a required option or flag was not provided."""

    def __init__(self, option: str = "", message: str | None = None):
        if message is None:
            if option:
                message = f"Required option '{option}' was not provided."
            else:
                message = "A required option was not provided."
        super().__init__(message)
        self.option = option


class OptionConflictError(Exception):
    """Raised when two mutually exclusive options are both set."""

    def __init__(self, option_a: str = "", option_b: str = "", message: str | None = None):
        if message is None:
            if option_a and option_b:
                message = f"Options '{option_a}' and '{option_b}' are mutually exclusive and cannot both be set."
            else:
                message = "Two mutually exclusive options are in conflict."
        super().__init__(message)
        self.option_a = option_a
        self.option_b = option_b


class OptionReadOnlyError(Exception):
    """Raised when an attempt is made to change an option that has been frozen/locked."""

    def __init__(self, option: str = "", message: str | None = None):
        if message is None:
            if option:
                message = f"Option '{option}' is read-only and cannot be changed after initialization."
            else:
                message = "This option is read-only."
        super().__init__(message)
        self.option = option


class InvalidOptionValueError(Exception):
    """Raised when an option is recognised but its value is out of the allowed domain."""

    def __init__(self, option: str = "", value=None, allowed=None, message: str | None = None):
        if message is None:
            parts = [f"Invalid value {value!r} for option '{option}'"] if option else [f"Invalid option value: {value!r}"]
            if allowed is not None:
                parts.append(f"Allowed values: {list(allowed)!r}")
            message = ". ".join(parts) + "."
        super().__init__(message)
        self.option = option
        self.value = value
        self.allowed = allowed
