from hyper_framework import MulticastCallback
from typing import Callable, List

result_list = []

# 實務範例：多個 handler 回應進度更新
on_progress: MulticastCallback[Callable[[int], None]] = MulticastCallback()

def log_progress(p: int):
    print(f"[LOG] progress={p}/100")
    result_list.append(f"[LOG] progress={p}/100")

def update_ui(p: int):
    print(f"UI -> Progress bar set to {p}%")
    result_list.append(f"UI -> Progress bar set to {p}%")

metrics: List[int] = []
def collect_metric(p: int):
    metrics.append(p)
    print(f"[METRIC] collected {p/100:.2%}")
    result_list.append(f"[METRIC] collected {p/100:.2%}")

# 註冊 handlers
on_progress.add(collect_metric)  ## for data collecting
on_progress.add(log_progress)  ## for terminal debug
on_progress.add(update_ui)  ## for user interface

print("=== ALL ===")
result_list.append("=== ALL ===")
# 廣播（所有已註冊的 handler 都會被呼叫）
on_progress(10)

print("\n=== AFTER REMOVAL ===")
result_list.append("=== AFTER REMOVAL ===")
# 移除某個 handler（- 回傳新 MulticastCallback；如要生效請重新指派或覆寫）
on_progress = on_progress - update_ui
on_progress(50)

print("\n=== COMBINED ===")
result_list.append("=== COMBINED ===")
# 合併兩個 MulticastCallback（回傳新物件，不改變原本的 operands）
extra = MulticastCallback[Callable[[int], None]]()
extra.add(lambda p: print(f"extra handler: {p}"))
extra.add(lambda p: result_list.append(f"extra handler: {p}"))
combined = on_progress + extra
combined(75)

print("\n=== RESULTS ===")
result_list.append("=== RESULTS ===")
print("metrics:", metrics)
result_list.append(f"metrics: {metrics}")

print(result_list)
assert result_list == [
    "=== ALL ===",
    "[METRIC] collected 10.00%",
    "[LOG] progress=10/100",
    "UI -> Progress bar set to 10%",
    
    "=== AFTER REMOVAL ===",
    "[METRIC] collected 50.00%",
    "[LOG] progress=50/100",
    
    "=== COMBINED ===",
    "[METRIC] collected 75.00%",
    "[LOG] progress=75/100",
    "extra handler: 75",
    
    "=== RESULTS ===",
    "metrics: [10, 50, 75]",
]