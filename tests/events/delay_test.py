from hyper_framework import DelayEventBusManager, IDelayEventBase

class OnSystemReady(IDelayEventBase): pass

bus = DelayEventBusManager()

# --- Producer（早於 consumer 啟動）---
def boot_system():
    # ... 初始化工作 ...
    bus.PublishEvent(OnSystemReady)   # 標記為已發生，觸發所有已等待的 callbacks

# --- Consumer（正常初始化順序）---
class EarlyModule:
    def _initialize(self):
        bus.RegisterEvent(OnSystemReady, self._on_ready)  # 入隊，等待 PublishEvent

    def _on_ready(self):
        print("EarlyModule: system ready")

# --- Consumer（晚初始化，事件已先發生）---
class LateModule:
    def _initialize(self):
        # PublishEvent 已執行過 → RegisterEvent 立即呼叫 _on_ready
        bus.RegisterEvent(OnSystemReady, self._on_ready)

    def _on_ready(self):
        print("LateModule: caught up!")

bus.Evoke(OnSystemReady)

## UNTESTED: 這裡的測試只是示範用，實際上應該要用 pytest 的 assert 來驗證行為是否正確。 ##