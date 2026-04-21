import weakref
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Type, Union

from isd_py_framework_sdk.events.DelayEventBase import IDelayEventBase, IDelayParsEventBase


class LazyListenerBase(ABC):
    """
        [ Event Replaying ]
            When Listener Will Be Lazy Initialized Or Instantiated After Observer Subscription.
            We Will Have To Trigger All The Events Bound With The Listener, To Make Sure The Workflow Is Correct !!
    """
    @abstractmethod
    def replay_subscribed_events(self, event_class_type: Union[Type[IDelayEventBase], Type[IDelayParsEventBase]]):
        DelayEventBusManager().Evoke(event_class_type)


class DelayEventBusManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_is_init"):
            # pending:
            ## should i record the instance's type or something else to make sure who is going to trigger the event ?
            ## however, this will increase the coupling of this module and may reduce the flexibility !!
            self.__delay_callbacks: Dict[Type, List[weakref.WeakMethod]] = {}
            self.__delay_callbacks_with_pars: Dict[Type, List[weakref.WeakMethod]] = {}
            # pending
            self._is_init = True


    def RegisterEvent(self, event_class_type: Union[Type[IDelayEventBase], Type[IDelayParsEventBase]], callback: Union[Callable, Callable[[IDelayParsEventBase], None]]):
        if callback is None:
            raise ValueError("callback cannot be None")

        if issubclass(event_class_type, IDelayEventBase):
            self.__delay_callbacks[event_class_type].append(weakref.WeakMethod(callback))
        elif issubclass(event_class_type, IDelayParsEventBase):
            self.__delay_callbacks_with_pars[event_class_type].append(weakref.WeakMethod(callback))

    def UnregisterEvent(self, event_class_type: Union[Type[IDelayEventBase], Type[IDelayParsEventBase]], callback: Union[Callable, Callable[[IDelayParsEventBase], None]]):
        if callback is None:
            raise ValueError("callback cannot be None")

        if issubclass(event_class_type, IDelayEventBase):
            target_list = self.__delay_callbacks.get(event_class_type, [])
        elif issubclass(event_class_type, IDelayParsEventBase):
            target_list = self.__delay_callbacks_with_pars.get(event_class_type, [])
        else:
            raise ValueError(f"This Type= {event_class_type} Is Not Allowed To Use Here !!")

        weak_callback = weakref.WeakMethod(callback)
        for wm in target_list:
            # wm 是 weakref.WeakMethod 物件，透過 .__eq__ 可以比較
            if wm == weak_callback:
                target_list.remove(wm)
                break


    def Evoke(self, event_class_type: Union[Type[IDelayEventBase], Type[IDelayParsEventBase]]):
        if issubclass(event_class_type, IDelayEventBase):
            target_list = self.__delay_callbacks.get(event_class_type, [])
        elif issubclass(event_class_type, IDelayParsEventBase):
            target_list = self.__delay_callbacks_with_pars.get(event_class_type, [])
        else:
            raise ValueError(f"This Type= {event_class_type} Is Not Allowed To Use Here !!")

        for wm in target_list:
            weak_callback = weakref.WeakMethod(wm)
            if weak_callback is not None:
                weak_callback()
            # pending:
            ## i think this is danger, and the design will only allow the evoke_function be executed once
            ## moreover, this may lead to memory-leak? slightly? due to empty lists reference are still maintained in ram
            target_list.remove(wm)
            # pending




