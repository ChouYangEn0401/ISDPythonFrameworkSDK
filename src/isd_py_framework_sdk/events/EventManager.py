import logging
import os
import weakref
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Type, Union, overload

from isd_py_framework_sdk.events.EventBase import IEventBase, IParsEventBase

# 用標準庫 logging（而非 message_logger）保持 events 子套件解耦、零相依。
# 消費端可用標準 logging 設定來決定要不要看這些訊息。
_logger = logging.getLogger(__name__)


def _reject_lambda(callback: Callable) -> None:
    """
    事件 callback 必須是「明確持有」的具名可呼叫物件——bound method
    (``self.method``) 或 module-level / static 函式。

    lambda（以及其他沒有強引用持有者的匿名 closure）會被本管理器的弱引用
    機制立即 GC 掉，造成無聲失效、且無法可靠解除註冊。因此在「註冊當下」
    就明確拒絕，而不是等到觸發時才神隱——把規則寫死，省掉逐案推理生命週期
    的 code-review 負擔。
    """
    if getattr(callback, "__name__", "") == "<lambda>":
        raise TypeError(
            "Event callbacks must be a named, strongly-held callable — a bound "
            "method like `self.method`, or a module-level / static function. "
            "Lambdas are rejected because the weak-reference registry would "
            "garbage-collect them immediately, causing silent failure and making "
            "them impossible to unregister. Assign your logic to a named "
            "method/function and register that instead."
        )


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
        _reject_lambda(callback)

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
            _logger.warning(
                "Callback for %s not found or already unregistered.",
                event_class.__name__,
            )

    def TriggerEvent(self, event_instance: Union[IEventBase, IParsEventBase]) -> None:
        if not isinstance(event_instance, (IEventBase, IParsEventBase)):
            raise TypeError("event_instance must be an instance of IEventBase or IParsEventBase.")

        event_type = type(event_instance)
        target_dict = self._get_target_event_lists(event_type)

        callbacks = target_dict.get(event_type, [])
        alive_callbacks: List[_WeakCallable] = []
        for weak_callback in callbacks:
            callback_func = weak_callback()

            # A 類：訂閱者已不在（持有者被刪 / GC，weakref 回 None）。
            # 這是正常生命週期、不是錯誤 → 安靜丟棄（不保留、不吵）。
            if callback_func is None:
                _logger.debug(
                    "Callback for %s was garbage collected; dropping from registry.",
                    event_type.__name__,
                )
                continue

            # 訂閱者仍存活：先保留註冊，確保「執行時拋例外」不會害它被退訂。
            alive_callbacks.append(weak_callback)

            # B 類：訂閱者活著但 body 拋例外 → 真正的 bug。
            # 大聲記錄（ERROR + traceback）但隔離：不連累其他 handler、也不退訂它。
            try:
                if isinstance(event_instance, IParsEventBase):
                    callback_func(event_instance)
                else:
                    callback_func()
            except Exception:
                _logger.exception(
                    "Handler for %s raised an exception; isolated, remaining "
                    "handlers continue and this handler stays registered.",
                    event_type.__name__,
                )

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


