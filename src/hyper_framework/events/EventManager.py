import os
import weakref
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Type, Union, overload

from hyper_framework.events.EventBase import IEventBase, IParsEventBase


class _WeakCallable:
    """
    Unified weak reference that handles both bound methods and plain callables.

    - Bound methods  → ``weakref.WeakMethod``  (avoids keeping the instance alive)
    - Plain callables → ``weakref.ref``          (module-level functions, static methods)
    """

    __slots__ = ("_ref",)

    def __init__(self, callback: Callable) -> None:
        if hasattr(callback, "__self__"):
            self._ref: Union[weakref.WeakMethod, weakref.ref] = weakref.WeakMethod(callback)
        else:
            self._ref = weakref.ref(callback)

    def __call__(self) -> Optional[Callable]:
        return self._ref()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _WeakCallable):
            return NotImplemented
        a, b = self._ref(), other._ref()
        if a is None or b is None:
            return False
        return a == b

    def __hash__(self) -> int:
        live = self._ref()
        return hash(live) if live is not None else 0


class SingletonEventManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialize_manager()
        return cls._instance

    def __initialize_manager(self):
        self.__registered_events: Dict[Type, List[_WeakCallable]] = defaultdict(list)
        self.__registered_pars_events: Dict[Type, List[_WeakCallable]] = defaultdict(list)

    def __init__(self):
        """
            key: class type,
            value: list of weak callables of callbacks
        """
        pass

    @overload
    def RegisterEvent(self, event_class: Type[IEventBase], callback: Callable[[], None]) -> None: ...
    @overload
    def RegisterEvent(self, event_class: Union[Type[IParsEventBase]], callback: Callable[[IParsEventBase], None]) -> None: ...
    def RegisterEvent(
            self,
            event_class: Union[Type[IEventBase], Type[IParsEventBase]],
            callback: Union[Callable[[], None], Callable[[IParsEventBase], None]]
    ) -> None:
        if callback is None:
            raise ValueError("Callback cannot be None")
        if not isinstance(event_class, type):
            raise TypeError("event_class must be an event class (e.g., OnMyEvent), not an instance.")

        target_dict = self._get_target_event_lists(event_class)
        target_dict[event_class].append(_WeakCallable(callback))

    @overload
    def UnregisterEvent(self, event_class: Type[IEventBase], callback: Callable[[], None]) -> None: ...
    @overload
    def UnregisterEvent(self, event_class: Type[IParsEventBase], callback: Callable[[IParsEventBase], None]) -> None: ...
    def UnregisterEvent(
            self,
            event_class: Union[Type[IEventBase], Type[IParsEventBase]],
            callback: Union[Callable[[], None], Callable[[IParsEventBase], None]]
    ) -> None:
        if callback is None:
            raise ValueError("Callback cannot be None")
        if not isinstance(event_class, type):
            raise TypeError("event_class must be an event class (e.g., OnMyEvent), not an instance.")

        target_dict = self._get_target_event_lists(event_class)
        target_list = target_dict.get(event_class, [])

        weak_callback_to_remove = _WeakCallable(callback)
        original_len = len(target_list)
        target_dict[event_class] = [
            wm for wm in target_list
            if wm() is not None and wm != weak_callback_to_remove
        ]
        if len(target_dict[event_class]) == original_len:
            print(f"Warning: Callback for {event_class.__name__} not found or already unregistered.")

    def TriggerEvent(self, event_instance: Union[IEventBase, IParsEventBase]) -> None:
        if not isinstance(event_instance, (IEventBase, IParsEventBase)):
            raise TypeError("event_instance must be an instance of IEventBase or IParsEventBase.")

        event_type = type(event_instance)
        target_dict = self._get_target_event_lists(event_type)

        callbacks = target_dict.get(event_type, [])
        alive_callbacks: List[_WeakCallable] = []
        for weak_callback in callbacks:
            callback_func = weak_callback()
            if callback_func is not None:
                try:
                    if isinstance(event_instance, IParsEventBase):
                        callback_func(event_instance)
                    elif isinstance(event_instance, IEventBase):
                        callback_func()
                    alive_callbacks.append(weak_callback)
                except TypeError as e:
                    print(
                        f"Error calling callback for {event_type.__name__}: {e}. Make sure callback signature matches event type.")
            else:
                print(f"Callback for {event_type.__name__} was garbage collected.")

        target_dict[event_type] = alive_callbacks

    def _get_target_event_lists(self, event_type: Type) -> (
                Dict[Type, List[_WeakCallable]] |
                Dict[Type, List[_WeakCallable]]
        ):
        if os.environ.get("EVENT_MANAGER_DEBUGGER"):
            self.__debugger(event_type)

        if issubclass(event_type, IParsEventBase):
            return self.__registered_pars_events
        elif issubclass(event_type, IEventBase):
            return self.__registered_events
        raise ValueError(f"Event type {event_type.__name__} is not a valid event base class (IEventBase or IParsEventBase).")

    def __debugger(self, event_type):
        print(f"\n--- Debugging _get_target_event_lists (in EventManager.py) ---")
        print(f"  Input event_type: {event_type}")
        print(f"  ID of input event_type: {id(event_type)}")
        print(f"  Module of input event_type: {event_type.__module__}")
        print(f"  MRO of input event_type: {event_type.__mro__}")

        print(f"\n  EventManager's IEventBase (from its own import):")
        print(f"    Class: {IEventBase}")
        print(f"    ID: {id(IEventBase)}")
        print(f"    Module: {IEventBase.__module__}")

        print(f"\n  EventManager's IParsEventBase (from its own import):")
        print(f"    Class: {IParsEventBase}")
        print(f"    ID: {id(IParsEventBase)}")
        print(f"    Module: {IParsEventBase.__module__}")


