# EventBase defines two kinds of events used across the framework:
# - `IEventBase`: parameterless events (callbacks are called with no args)
# - `IParsEventBase`: parameterized events (callbacks receive the event instance)
# SingletonEventManager dispatches to callbacks according to which base the
# concrete event class inherits from.
from abc import ABC
from dataclasses import dataclass


class IEventBase(ABC):
    pass

@dataclass
class IParsEventBase(ABC):
    ## 繼承者仍要繼續用 @dataclass 裝飾自己，才能有 __init__ 等方法
    ## 此處寫出來只是用作提醒，讓架構可以更快被掌握
    pass

