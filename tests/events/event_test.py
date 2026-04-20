from hyper_framework.events_bus import SingletonEventManager, IEventBase, IParsEventBase
from dataclasses import dataclass


result_list= []

class OnJobDone(IEventBase): pass

@dataclass
class OnProgress(IParsEventBase):
    percent: float

em = SingletonEventManager()

# --- 綁定方法 callback ---
class Worker:
    def on_done(self):
        print("Job done!")
        result_list.append("Job done!")

    def on_inner_progress(self, e: OnProgress):
        print(f"Inner Progress: {e.percent:.0%}")
        result_list.append(f"Inner Progress: {e.percent:.0%}")

    @staticmethod
    def on_progress(e: OnProgress):
        print(f"On Progress: {e.percent:.0%}")
        result_list.append(f"On Progress: {e.percent:.0%}")

    def subscribe(self):
        em.RegisterEvent(OnJobDone, self.on_done)
        em.RegisterEvent(OnProgress, self.on_progress)

    def unsubscribe(self):
        em.UnregisterEvent(OnJobDone, self.on_done)
        em.UnregisterEvent(OnProgress, self.on_progress)

# --- 普通函式 callback ---
def handle_done():
    print("Done (plain function)!")
    result_list.append("Done (plain function)!")


print("=== OnJobDone ===")
result_list.append("=== OnJobDone ===")
em.RegisterEvent(OnJobDone, handle_done)
em.TriggerEvent(OnJobDone())
em.UnregisterEvent(OnJobDone, handle_done)

print("=== OnProgress ===")
result_list.append("=== OnProgress ===")
em.RegisterEvent(OnProgress, Worker.on_progress)
em.TriggerEvent(OnProgress(percent=0.75))
em.UnregisterEvent(OnProgress, Worker.on_progress)

print("=== Worker Events ===")
result_list.append("=== Worker Events ===")
w = Worker()
w.subscribe()
em.RegisterEvent(OnProgress, w.on_inner_progress)
em.TriggerEvent(OnJobDone())
em.TriggerEvent(OnProgress(percent=0.5))

assert result_list == [
    "=== OnJobDone ===",
    "Done (plain function)!",
    "=== OnProgress ===",
    "On Progress: 75%",
    "=== Worker Events ===",
    "Job done!",
    "On Progress: 50%",
    "Inner Progress: 50%",
]
