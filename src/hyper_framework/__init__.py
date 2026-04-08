"""
ISD Python Framework — Public API
"""
from ._version import __version__
from .base.Singleton import SingletonMetaclass
from .events.EventBase import IEventBase, IParsEventBase
from .events.EventManager import SingletonEventManager
from .events.DelayEventBusManager import DelayEventBusManager, IDelayEventBase, IDelayParsEventBase
from .events.MulticastCallback import MulticastCallback
from .message_logger.SingletonSystemLogger import SingletonSystemLogger
from .decorators.decorators_pack import function_timer, timed_and_conditional_return, deprecated, battered
from .exceptions.exceptions import (
    WrongOptionException,
    WrongImplementationException,
    UnhandledConditionError,
    RepeatedInitializationError,
)

__all__ = [
    "__version__",
    # core
    "SingletonMetaclass",
    # events
    "IEventBase",
    "IParsEventBase",
    "SingletonEventManager",
    "IDelayEventBase",
    "IDelayParsEventBase",
    "DelayEventBusManager",
    "MulticastCallback",
    # logger
    "SingletonSystemLogger",
    # decorators
    "function_timer",
    "timed_and_conditional_return",
    "deprecated",
    "battered",
    # exceptions
    "WrongOptionException",
    "WrongImplementationException",
    "UnhandledConditionError",
    "RepeatedInitializationError",
]
