"""
Script 式自我驗證（非 pytest 收集；請用 `python tests/events/robustness_test.py` 跑）。

涵蓋 EventManager 三項韌性行為：
  1. lambda 在 RegisterEvent 當下就被拒絕（不准無聲消失的匿名 closure）。
  2. 某個 handler 拋例外時「隔離」：其他 handler 照跑、拋例外的也不被退訂。
  3. 訂閱者的持有者被 GC 後，weakref 回 None → 安靜丟棄、不崩潰。
"""
import gc
import logging

from dataclasses import dataclass

from isd_py_framework_sdk.events import SingletonEventManager, IEventBase, IParsEventBase

# 這些測試會故意觸發 handler 例外與 GC 丟棄，EventManager 會用 logging 記錄；
# 把 events logger 靜音，避免 traceback 污染測試輸出（不影響行為驗證）。
logging.getLogger("isd_py_framework_sdk.events").setLevel(logging.CRITICAL)

em = SingletonEventManager()


class OnPing(IEventBase):
    pass


@dataclass
class OnValue(IParsEventBase):
    value: int


# --- 1. lambda 一律在註冊當下被拒絕 ----------------------------------------
print("=== 1. lambda rejected at register ===")
rejected = False
try:
    em.RegisterEvent(OnPing, lambda: None)
except TypeError as e:
    rejected = True
    assert "Lambda" in str(e) or "lambda" in str(e), str(e)
assert rejected, "lambda 應該在 RegisterEvent 當下被 raise，卻被接受了"

# payload 事件的 lambda 也要被擋
rejected_pars = False
try:
    em.RegisterEvent(OnValue, lambda e: None)
except TypeError:
    rejected_pars = True
assert rejected_pars, "payload 事件的 lambda 也應被拒絕"
print("  OK — lambda 在註冊時即被拒絕")


# --- 2. handler 拋例外時隔離：其他照跑、拋例外者不被退訂 ----------------------
print("=== 2. exception isolation ===")
calls = []


def boom():
    calls.append("boom-called")
    raise RuntimeError("handler 內部炸了")


def good():
    calls.append("good-called")


em.RegisterEvent(OnPing, boom)
em.RegisterEvent(OnPing, good)

em.TriggerEvent(OnPing())
# boom 先註冊先觸發、雖然拋例外，good 仍應被呼叫
assert calls == ["boom-called", "good-called"], calls

# 再觸發一次：boom 不應因為上次拋例外而被退訂，兩者都要再被呼叫
calls.clear()
em.TriggerEvent(OnPing())
assert calls == ["boom-called", "good-called"], f"拋例外的 handler 被退訂了：{calls}"

em.UnregisterEvent(OnPing, boom)
em.UnregisterEvent(OnPing, good)
print("  OK — 一個 handler 拋例外不連累別人、也不被退訂")


# --- 3. 持有者被 GC → weakref 回 None → 安靜丟棄、不崩潰 ----------------------
print("=== 3. dead callback silently dropped ===")
hits = []


class ShortLived:
    def on_value(self, e: OnValue):
        hits.append(e.value)


obj = ShortLived()
em.RegisterEvent(OnValue, obj.on_value)

em.TriggerEvent(OnValue(value=1))
assert hits == [1], hits

# 刪掉唯一持有者並強制回收；WeakMethod 應失效
del obj
gc.collect()

# 不應崩潰；死掉的 callback 被安靜丟棄，hits 不再增加
em.TriggerEvent(OnValue(value=2))
assert hits == [1], f"持有者已 GC，callback 不該再被觸發：{hits}"
print("  OK — 持有者 GC 後 callback 被安靜丟棄、TriggerEvent 不崩潰")


print("\n✔ all robustness checks passed")
