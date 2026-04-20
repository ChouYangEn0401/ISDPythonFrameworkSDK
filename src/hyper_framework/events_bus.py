"""
hyper_framework.events_bus — 事件系統的短路徑別名。

等同於個別從 hyper_framework.events.* 匯入，提供更簡潔的 namespace：
    from hyper_framework.events_bus import SingletonEventManager, IEventBase, ...
"""

from .events.EventBase import IEventBase, IParsEventBase
from .events.EventManager import SingletonEventManager
from .events.DelayEventBusManager import (
    DelayEventBusManager,
    IDelayEventBase,
    IDelayParsEventBase,
)
from .events.MulticastCallback import MulticastCallback

__all__ = [
    "IEventBase",
    "IParsEventBase",
    "SingletonEventManager",
    "DelayEventBusManager",
    "IDelayEventBase",
    "IDelayParsEventBase",
    "MulticastCallback",
]
