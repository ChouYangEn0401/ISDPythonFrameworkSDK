from abc import abstractmethod
from typing import Generic, Protocol, TypeVar, Type, runtime_checkable


SingletonType = TypeVar("SingletonType", bound="SingletonProtocol")

@runtime_checkable
class SingletonProtocol(Protocol):
    @classmethod
    def __new__(cls: Type[SingletonType]) -> SingletonType:
        pass
