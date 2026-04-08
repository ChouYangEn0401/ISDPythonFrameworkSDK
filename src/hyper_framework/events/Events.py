import os
import pandas as pd
from typing import Dict, Tuple, Literal
from dataclasses import dataclass

from hyper_framework.events.EventBase import IEventBase, IParsEventBase


def __module_debugger():
    import sys
    import os
    import traceback  # 確保有導入 traceback

    # --- 模組載入診斷函數 ---
    current_module_path = os.path.abspath(__file__)
    found_in_sys_modules = []

    for module_name, module_obj in sys.modules.items():
        if module_obj is not None:
            # 在訪問 __file__ 之前，確保它不是 None
            if hasattr(module_obj, '__file__') and module_obj.__file__ is not None:
                try:
                    # 比較模組的真實文件路徑
                    if os.path.abspath(module_obj.__file__) == current_module_path:
                        found_in_sys_modules.append(module_name)
                except Exception as e:  # 捕捉更廣泛的異常，以防萬一
                    # print(f"Debug: Error checking module {module_name}: {e}")
                    pass
            # else:
            #     print(f"Debug: Module {module_name} has no __file__ or __file__ is None.")

    if len(found_in_sys_modules) > 1:
        print(f"\n--- 警告：'{current_module_path}' 被重複載入 ---")
        print(f"  已載入的名稱: {found_in_sys_modules}")
        print(f"  重複載入者為：")
        traceback.print_stack(limit=10)  # 限制堆棧深度，避免過長
        print("--- 警告結束 ---\n")
    elif len(found_in_sys_modules) == 1:
        print(f"Debug: '{current_module_path}' 首次以名稱 '{found_in_sys_modules[0]}' 載入。")
    else:
        # 這通常發生在模組正在載入過程中，它自己還沒完全進入 sys.modules
        print(f"Debug: '{current_module_path}' 正在首次載入中 (尚未完全進入 sys.modules)。")


if SingletonEnvManager().get_env("EVENT_MANAGER_DEBUGGER"):
    # 立即執行診斷函數
    __module_debugger()

@dataclass
class OnMainWindow1_TreeviewUpdateWithNewDF(IParsEventBase):
    module_name: str
    new_df: pd.DataFrame
    run_mode: Literal["append", "replace"]


def __debugger():
    # --- Debugging Info ---
    print(f"\n--- Debugging Events.py Load ---")
    print(f"Events.py's IEventBase ID: {id(IEventBase)}, Module: {IEventBase.__module__}")
    print(f"Events.py's IParsEventBase ID: {id(IParsEventBase)}, Module: {IParsEventBase.__module__}")
    print(f"Events.py's OnModuleD_MainWindowTreeviewUpdate ID: {id(OnModuleD_MainWindowTreeviewUpdate)}, Module: {OnModuleD_MainWindowTreeviewUpdate.__module__}")

if SingletonEnvManager().get_env("EVENT_MANAGER_DEBUGGER"):
    __debugger()
