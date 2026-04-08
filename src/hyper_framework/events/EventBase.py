# EventBase defines two kinds of events used across the framework:
# - `IEventBase`: parameterless events (callbacks are called with no args)
# - `IParsEventBase`: parameterized events (callbacks receive the event instance)
# SingletonEventManager dispatches to callbacks according to which base the
# concrete event class inherits from.
from abc import ABC


class IEventBase(ABC):
    pass

class IParsEventBase(ABC):
    pass

