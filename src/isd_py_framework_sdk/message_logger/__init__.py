"""
message_logger - structured logging with composable output adapters.

Recommended entrypoint:
    from isd_py_framework_sdk.message_logger import (
        SingletonSystemLogger,
        DarkThemeTerminalAdapter,
        FileAdapter,
    )

The top-level public API intentionally keeps the common path small:
    - create/get the singleton logger
    - add concrete adapters
    - optionally subclass LoggerAdapterBase for a custom output

Advanced base classes remain importable for compatibility, but are not part of
``__all__`` so general users do not need to learn the internal inheritance tree.
"""

from .base.levels import LogLevelLiteral, LevelOrder
from .base.LoggerAdapterBase import LoggerAdapterBase
from .base.LoggerBase import LoggerBase
from .adapters import (
    AbstractTerminalAdapterBase,
    DarkThemeTerminalAdapter,
    LightThemeTerminalAdapter,
    FileAdapter,
    AbstractTkinterAdapterBase,
    DarkThemeTkinterAdapter,
    LightThemeTkinterAdapter,
    TkLabelAdapter,
    DarkThemeTkLabelAdapter,
    LightThemeTkLabelAdapter,
    TtkLabelAdapter,
    DarkThemeTtkLabelAdapter,
    LightThemeTtkLabelAdapter,
    LocalHTTPAdapter,
    QueuedSocketAdapter,
    HTMLAdapter,
    HTTPAdapter,
    DBAdapter,
    WebsocketAdapter,
)
from .SingletonSystemLogger import SingletonSystemLogger


def get_logger(
    *adapters: LoggerAdapterBase,
    clear: bool = False,
) -> SingletonSystemLogger:
    """
    Return the global logger and optionally attach adapters.

    ``clear=True`` resets previously registered adapters before adding the new
    ones. The default is non-destructive because this logger is a singleton.
    """
    logger = SingletonSystemLogger()
    if clear:
        logger.clear_adapters()
    for adapter in adapters:
        logger.register_adapter(adapter)
    return logger


def configure_logger(
    *adapters: LoggerAdapterBase,
    clear: bool = True,
) -> SingletonSystemLogger:
    """
    Configure the global logger for an application startup path.

    Unlike ``get_logger()``, this clears existing adapters by default because it
    is meant for one-time setup.
    """
    return get_logger(*adapters, clear=clear)


__all__ = [
    # logger
    "SingletonSystemLogger",
    "get_logger",
    "configure_logger",
    # extension point
    "LoggerAdapterBase",
    # levels
    "LogLevelLiteral",
    "LevelOrder",
    # common adapters
    "DarkThemeTerminalAdapter",
    "LightThemeTerminalAdapter",
    "FileAdapter",
    "DarkThemeTkinterAdapter",
    "LightThemeTkinterAdapter",
    "DarkThemeTkLabelAdapter",
    "LightThemeTkLabelAdapter",
    "DarkThemeTtkLabelAdapter",
    "LightThemeTtkLabelAdapter",
    "LocalHTTPAdapter",
    "QueuedSocketAdapter",
]
