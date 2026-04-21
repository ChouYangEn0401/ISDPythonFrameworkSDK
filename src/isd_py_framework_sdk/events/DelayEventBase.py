from abc import ABC
from dataclasses import dataclass

class IDelayEventBase(ABC):
    pass

@dataclass
class IDelayParsEventBase(ABC):
    ## 繼承者仍要繼續用 @dataclass 裝飾自己，才能有 __init__ 等方法
    ## 此處寫出來只是用作提醒，讓架構可以更快被掌握
    pass

