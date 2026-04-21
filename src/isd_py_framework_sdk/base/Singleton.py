from abc import abstractmethod
from typing import Dict, Type, Any

class SingletonMetaclass(type):
    """
        這是一個元類，用於為任何類別自動實現單例模式。

        它接管了類別的實例化過程，確保每個類別只會被創建一次實例。
        所有被這個元類創建的單例實例都會儲存在一個私有字典中，
        以實現集中的管理。
    """
    _instances: Dict[Type, Any] = {}

    def __call__(cls: Type, *args: Any, **kwargs: Any) -> Any:
        """
            當類別被呼叫（例如 MyClass()）時，此方法會被觸發。
            它會檢查該類別是否已存在實例，若無，則創建一個並儲存。
        """
        # 檢查該類別是否已經存在於我們的實例字典中
        if cls not in cls._instances:
            # 如果不存在，則呼叫父類（type）的__call__方法來創建一個新實例
            instance = super().__call__(*args, **kwargs)

            # 在實例首次創建後，呼叫可選的初始化鉤子
            # 這讓類別可以在單例實例首次創建時執行一次性的初始化邏輯
            if hasattr(instance, '_initialize_manager'):
                instance._initialize_manager()

            # 將新實例儲存在字典中
            cls._instances[cls] = instance

        # 永遠返回字典中已存在的實例
        return cls._instances[cls]
