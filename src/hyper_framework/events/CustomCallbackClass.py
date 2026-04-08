from typing import List, TypeVar, Generic, Callable, Any

"""
知識點補充：
1. 過早的彈性（"You Ain't Gonna Need It" - YAGNI 原則）可能導致過度設計、不必要的複雜性，甚至引入更多錯誤。先求穩固，再求靈活。
2. 優先考慮「單一職責原則」 (Single Responsibility Principle - SRP)： SRP 是 SOLID 原則中的第一個，也是基石。它主張一個類別或模組應該只有一個改變的理由。
3. 再考慮「擴充性」 (Extensibility)： 良好的擴充性通常是 SRP 的自然結果。
"""


# --- 通用的 Callback 管理器 (使用 Generic 和 TypeVar) ---
T_Callable = TypeVar('T_Callable', bound=Callable[..., Any]) # bound=Callable[..., Any] 表示 T_Callable 必須是一個可呼叫的物件
class GenericCallbacksClass(Generic[T_Callable]):
    """
        T_Callable 是一個 TypeVar，用來表示任何 Callable 型別
        ParamSpec 可以更精確地綁定參數簽名，但在這裡使用 Callable[..., Any] 更通用一些
        但如果你需要更嚴格的參數綁定，可以使用 ParamSpec 和 Concatenate
        from typing import ParamSpec, Concatenate
        P = ParamSpec('P')
        T_Callable = TypeVar('T_Callable', bound=Callable[P, Any])
    """

    def __init__(self, b_debug_print = False):
        self._callbacks: List[T_Callable] = []
        self.b_debug_print = b_debug_print

    def add(self, callback: T_Callable):
        """
            直覺來看，會覺得是把某個東西加到某個集合來做管理，所以加入項目應該是以element的身分。
            所以應該選用 T_Callable，也就是 self._callbacks 的 Element 的 Type。
        """
        self._callbacks.append(callback)

    def remove(self, callback: T_Callable):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    # 重載加法運算子，用於合併兩個 GenericCallbacksClass
    def __add__(self, other: 'GenericCallbacksClass[T_Callable]') -> 'GenericCallbacksClass[T_Callable]':
        """
            直覺來看，會覺得是把兩個相當的東西做加總(例如單位相同)，所以具有對稱性與交換率。
            所以應該選用 GenericCallbacksClass[T_Callable]，也就是 self 的 Type。
        """
        if not isinstance(other, GenericCallbacksClass):
            return NotImplemented
        new_manager = GenericCallbacksClass[T_Callable]()  ## 不可變性 / Immutability, 確保 z = x + y 是新物件返回而非修改 x
        new_manager._callbacks.extend(self._callbacks)
        new_manager._callbacks.extend(other._callbacks)
        return new_manager

    # 重載減法運算子，用於從管理器中移除 callback
    def __sub__(self, callback_to_remove: T_Callable) -> 'GenericCallbacksClass[T_Callable]':
        if not isinstance(callback_to_remove, Callable): # 這裡判斷 Callable 比較泛
            return NotImplemented
        new_manager = GenericCallbacksClass[T_Callable]()  ## 不可變性 / Immutability, 確保 z = x - y 是新物件返回而非修改 x
        for cb in self._callbacks:
            if cb != callback_to_remove:
                new_manager._callbacks.append(cb)
        return new_manager

    # __call__ 方法現在可以接受任何參數，並將這些參數傳遞給所有註冊的 callback
    def __call__(self, *args: Any, **kwargs: Any):
        if self.b_debug_print:
            print("\n--- 執行所有註冊的 callbacks ---")
        for callback in self._callbacks:
            try:
                callback(*args, **kwargs) # 將接收到的參數轉發給每個 callback
            except TypeError as e:
                # 這裡的 TypeError 可能因為 callback 接收的參數與 __call__ 傳入的不符
                print(f"錯誤：Callback {callback.__class__.__name__ if hasattr(callback, '__class__') else callback.__name__} 呼叫失敗，可能是參數不符: {e}")
            except Exception as e:
                print(f"錯誤：Callback {callback.__class__.__name__ if hasattr(callback, '__class__') else callback.__name__} 執行時發生未知錯誤: {e}")
        if self.b_debug_print:
            print("--- Callbacks 執行完畢 ---\n")



if __name__ == "__main__":
    # --- 範例使用 (搭配不同參數簽名的 callback) ---

    # Callback 類型 1: 無參數
    def greet():
        print("Hello!")

    # Callback 類型 2: 帶一個 int 參數
    def show_number(num: int):
        print(f"The number is: {num}")

    # Callback 類型 3: 帶一個 str 和一個 bool 參數
    def process_item(item_name: str, is_active: bool):
        print(f"Processing item '{item_name}', active: {is_active}")

    # 創建一個管理無參數 callback 的管理器
    manager_no_args = GenericCallbacksClass[Callable[[], None]]()
    manager_no_args.add(greet)
    manager_no_args() # 執行：Hello!

    # 創建一個管理帶一個 int 參數 callback 的管理器
    manager_int_arg = GenericCallbacksClass[Callable[[int], None]]()
    manager_int_arg.add(show_number)
    manager_int_arg(123) # 執行：The number is: 123

    # 創建一個管理帶 str 和 bool 參數 callback 的管理器
    manager_item_args = GenericCallbacksClass[Callable[[str, bool], None]]()
    manager_item_args.add(process_item)
    manager_item_args("Laptop", True) # 執行：Processing item 'Laptop', active: True

    # 注意：嘗試將不符簽名的 callback 加入會被靜態型別檢查器警告
    # manager_no_args.add(show_number) # MyPy 警告: Argument "callback" to "add" of "GenericCallbacksClass" has incompatible type "Callable[[int], None]"; expected "Callable[[], None]"

    # 合併不同 Generic 類型的管理器會被 MyPy 警告，因為它們的 TypeVar 不匹配
    # combined_m = manager_no_args + manager_int_arg # MyPy 警告

