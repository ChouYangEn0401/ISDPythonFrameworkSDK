from typing import TypeVar, Type, Generic, Protocol, runtime_checkable

T = TypeVar("T", bound="EntityProtocol")

@runtime_checkable
class EntityProtocol(Protocol):
    @classmethod
    def find_by_id(cls: Type[T], id: int) -> T:
        ...

class EntityBase(Generic[T]):
    _db = {
        1: {"name": "Apple"},
        2: {"name": "Banana"},
    }

    @classmethod
    def find_by_id(cls: Type[T], id: int) -> T:
        print(f"Querying {cls.__name__} by ID: {id}")
        data = cls._db.get(id, {})
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance

class Product(EntityBase["Product"]):
    name: str = ""

if __name__ == "__main__":
    # 使用
    p = Product.find_by_id(1)
    print(p.name)  # Apple
