from weakref import WeakMethod
from collections import defaultdict
from typing import Callable, Dict, List, Type, Union, overload

## 路徑要寫一樣(src都要寫)，不然python會把他當成兩種物件，導致解析的時候出現不同，然後就會整個炸掉
from src.hyper_framework.app_env_settings.EnvironmentVariable import SingletonEnvManager
from src.hyper_framework.events.Events import IEventBase, IParsEventBase


class SingletonEventManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialize_manager()
        return cls._instance

    def __initialize_manager(self):
        self.__registered_events: Dict[Type, List[WeakMethod[Callable[[], None]]]] = defaultdict(list)
        self.__registered_pars_events: Dict[Type, List[WeakMethod[Callable[[IParsEventBase], None]]]] = defaultdict(list)

    def __init__(self):
        """
            key: class type,
            value: list of WeakMethod of callbacks
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
    ):
        if callback is None:
            raise ValueError("Callback cannot be None")
        if not isinstance(event_class, type):
            raise TypeError("event_class must be an event class (e.g., OnMyEvent), not an instance.")

        target_dict = self._get_target_event_lists(event_class)
        target_dict[event_class].append(WeakMethod(callback))
        # print(f"Registered {callback.__name__} for {event_class.__name__}")  # 用於偵錯

    @overload
    def UnregisterEvent(self, event_class: Type[IEventBase], callback: Callable[[], None]) -> None: ...
    @overload
    def UnregisterEvent(self, event_class: Type[IParsEventBase], callback: Callable[[IParsEventBase], None]) -> None: ...
    def UnregisterEvent(
            self,
            event_class: Union[Type[IEventBase], Type[IParsEventBase]],
            callback: Union[Callable[[], None], Callable[[IParsEventBase], None]]
    ):
        if callback is None: ## 可留可不留，反正也不能解綁空值
            raise ValueError("Callback cannot be None")
        if not isinstance(event_class, type):
            raise TypeError("event_class must be an event class (e.g., OnMyEvent), not an instance.")

        target_dict = self._get_target_event_lists(event_class)
        target_list = target_dict.get(event_class, [])
        # print(f"Unregistered {callback.__name__} for {event_class.__name__}")  # 用於偵錯

        weak_callback_to_remove = WeakMethod(callback)
        # 過濾掉弱參考，只保留存活且不是目標的參考
        original_len = len(target_list)
        target_dict[event_class] = [
            wm for wm in target_list
            if wm() is not None and wm != weak_callback_to_remove
        ]
        if len(target_dict[event_class]) == original_len:
            print(f"Warning: Callback for {event_class.__name__} not found or already unregistered.")

    def TriggerEvent(self, event_instance: Union[IEventBase, IParsEventBase]):
        if not isinstance(event_instance, (IEventBase, IParsEventBase)):
            raise TypeError("event_instance must be an instance of IEventBase or IParsEventBase.")

        event_type = type(event_instance)
        target_dict = self._get_target_event_lists(event_type)

        callbacks = target_dict.get(event_type, [])
        alive_callbacks = []
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
                # pass
                print(f"Callback for {event_type.__name__} was garbage collected.")

        target_dict[event_type] = alive_callbacks  # 清理失效的參考
        # import sys
        # print("del event", sys.getrefcount(event_instance))
        # del event_instance ## 實際上不用，因為出了函數 event_instance 就沒有 reference 了，所以會自己刪掉。那如果外面寫的不對，加了也刪除不掉。

    def _get_target_event_lists(self, event_type: Type) -> (
                Dict[Type, List[WeakMethod[Callable[[], None]]]] |
                Dict[Type, List[WeakMethod[Callable[[IParsEventBase], None]]]]
        ):
        if SingletonEnvManager().get_env("EVENT_MANAGER_DEBUGGER"):
            self.__debugger(event_type)

        # 優先檢查 IParsEventBase，因為它可能繼承自 IEventBase
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


