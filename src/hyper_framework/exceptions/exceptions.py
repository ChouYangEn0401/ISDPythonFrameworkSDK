import inspect


class WrongOptionException(Exception):
    def __init__(self, option, message=None):
        if message is None:
            message = f"No Mode Found !! Wrong：`{option}` !!"
        super().__init__(message)
        # self.option = option  ## not sure if need or not

class WrongImplementationException(Exception):
    def __init__(self, restriction: str, message: str = None):
        """
        當函式被錯誤使用時觸發的例外。

        Args:
            restriction (str): 描述不允許操作的具體限制。
            message (str, optional): 自訂的錯誤訊息。如果未提供，則會產生一個預設訊息。
        """
        if message is None:
            message = f"此函式不允許這樣使用 !! \n 限制：{restriction}"
        super().__init__(message)
        self.restriction = restriction

    def __str__(self):
        """
        提供更詳細的例外訊息，包含發生錯誤的類別。
        """
        # 嘗試找出呼叫此例外的類別
        frame = inspect.currentframe().f_back
        while frame:
            if 'self' in frame.f_locals:
                calling_class = frame.f_locals['self'].__class__.__name__
                return f"錯誤：在類別 '{calling_class}' 中發生 WrongImplementationException。\n{super().__str__()}"
            frame = frame.f_back
        return super().__str__()

class UnhandledConditionError(Exception):
    def __init__(self, message=None, **kwargs):
        """
        當 if-elif-else 結構未能處理某種狀況時拋出的錯誤。

        Args:
            message (str, optional): 自訂的錯誤訊息。如果未提供，將自動生成。
            **kwargs: 任何你希望在錯誤訊息中顯示的變數名稱和其值。
                      例如：llb=self.llb, lla=self.lla, result_=result_
        """
        if message is None:
            # 建立一個包含所有傳入變數的字串
            details = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            if details:
                message = f"程式條件判斷未涵蓋此狀態！未處理的詳細資訊: {details}"
            else:
                message = "程式條件判斷未涵蓋此狀態！"

        super().__init__(message)
        # self.details 屬性，如果你以後需要程式化地訪問這些細節
        self.details = kwargs

class RepeatedInitializationError(Exception):
    """當一個物件被重複初始化或註冊時拋出此例外。"""
    def __init__(self, message="這個物件已被初始化，無法再次執行此操作。"):
        super().__init__(message)
