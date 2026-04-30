from concurrent.futures import ProcessPoolExecutor, as_completed
import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from exps_src.isd_py_framework_sdk.monitoring.looped_function_timer import (
    LoopedFunctionTimer,
    LoopedFunction_timer_decorator,
    MultiProcessLoopedFunctionTimer,
)


### --- 各種單元測試 --- ###
def unit_test__single_thread():
    total = 100
    timer = LoopedFunctionTimer(total=total, inline=True, level="CHECKPOINT")

    print(f"<<< 啟動 LoopTimer 單進程任務 (Total Tasks: {total}) >>>")
    for i in range(total):
        timer.start()
        time.sleep(0.01)
        timer.stop()
        timer.msg(i + 1, bar=True)
    timer.show_info()


class _LocalTest:
    def __init__(self, total_tasks):
        self.total_tasks = total_tasks
        self.timer = LoopedFunctionTimer(total=total_tasks)

    @LoopedFunction_timer_decorator
    def process_task1(self, task_id):
        time.sleep(0.1)
        return f"Task {task_id} processed"

    @LoopedFunction_timer_decorator
    def process_task2(self, task_id):
        time.sleep(0.5)
        return f"Task {task_id} processed"

    def run1(self):
        self.timer.reset()
        for task_id in range(self.total_tasks):
            self.process_task1(task_id)
        self.timer.end_msg()

    def run2(self):
        self.timer.reset()
        for task_id in range(self.total_tasks):
            self.process_task2(task_id)
        self.timer.show_info()


def unit_test__decorator():
    print("<<< Decorator Test >>>")
    task_processor = _LocalTest(total_tasks=20)
    task_processor.run1()
    task_processor.run2()


def _heavy_task(data_item):
    sleep_time = 0.01
    time.sleep(sleep_time)
    return f"Processed item {data_item} in {sleep_time:.2f}s"


def unit_test__multiprocess():
    total_items = 10000
    max_workers = os.cpu_count() or 4

    multi_timer = MultiProcessLoopedFunctionTimer(total=total_items, inline=True, level="CHECKPOINT")

    print(
        f"<<< 啟動 MultiLoopTimer 多工進度條 (Workers: {max_workers}, Total Tasks: {total_items}) >>>"
    )
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_heavy_task, i): i for i in range(total_items)}

        multi_timer.start()
        for future in as_completed(futures):
            try:
                future.result()
                multi_timer.task_completed(b_show_msg=True, bar=True)
            except Exception as e:
                # 保持 legacy 測試行為，不中斷流程。
                multi_timer.logger.log(f"Task failed: {e}", "ERROR")
        multi_timer.stop()

    multi_timer.show_info()


if __name__ == "__main__":
    unit_test__single_thread()
    unit_test__decorator()
    unit_test__multiprocess()
