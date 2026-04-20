from hyper_framework.events import IEventBase, IParsEventBase
from dataclasses import dataclass

# 無參數事件
class OnDataReady(IEventBase): pass

# 帶參數事件
@dataclass
class OnDataLoaded(IParsEventBase):
    row_count: int
    source: str