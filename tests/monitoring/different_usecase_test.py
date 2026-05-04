from concurrent.futures import ProcessPoolExecutor, as_completed, wait, FIRST_COMPLETED
import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from isd_py_framework_sdk.monitoring.looped_function_timer import (
    ColorLiteral,
    LoopedFunctionTimer,
    LoopedFunction_timer_decorator,
    MultiProcessLoopedFunctionTimer,
)

SINGLE_THREAD_COLOR: ColorLiteral = "yellow"
DECORATOR_COLOR: ColorLiteral = "purple"
MULTIPROCESS_COLOR: ColorLiteral = "sky_blue"


### --- 各種單元測試 --- ###
def unit_test__single_thread():
    total = 100
    timer = LoopedFunctionTimer(
        total=total,
        inline=True,
        level="CHECKPOINT",
        color=SINGLE_THREAD_COLOR,
    )

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
        self.timer = LoopedFunctionTimer(total=total_tasks, color=DECORATOR_COLOR)

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

    multi_timer = MultiProcessLoopedFunctionTimer(
        total=total_items,
        inline=True,
        level="CHECKPOINT",
        color=MULTIPROCESS_COLOR,
    )

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


# ---------------------------------------------------------------------------
# 補充測試：來自 legacy old_test.py 的「節流雙重迴圈」模式
# 使用 wait(FIRST_COMPLETED) 防止 Future 佇列過度飽和，每個子任務呼叫 task_completed()
# ---------------------------------------------------------------------------

class _HighCostObj:
    """模擬高成本初始化物件（外層迴圈每輪建立一次）"""

    def __init__(self, j: int):
        self.j_value = j

    def process(self, i: int) -> int:
        return self.j_value * i


def _throttled_task(i: int, j_value: int) -> dict:
    """工作函式：模擬計算任務（不傳整個物件，只傳可序列化的值）"""
    time.sleep(0.001)
    return {"i": i, "j": j_value, "result": j_value * i}


def unit_test__multiprocess_throttled():
    """
    節流雙重迴圈模式（對應 legacy old_test.py）。
    外層迴圈高成本，內層迴圈提交任務；透過 wait(FIRST_COMPLETED) 防止佇列爆炸。
    """
    OUTER_N = 5        # 外層迴圈（高成本物件）
    INNER_M = 200      # 內層迴圈（子任務）
    TOTAL = OUTER_N * INNER_M
    MAX_WORKERS = min(os.cpu_count() or 4, 4)
    MAX_PENDING = MAX_WORKERS * 2

    timer = MultiProcessLoopedFunctionTimer(
        total=TOTAL, inline=True, color="red"
    )

    print(f"\n<<< 節流雙重迴圈測試 (Workers={MAX_WORKERS}, Limit={MAX_PENDING}, Total={TOTAL}) >>>")

    results = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        active_futures: set = set()
        timer.start()

        for j in range(OUTER_N):
            obj = _HighCostObj(j)
            for i in range(INNER_M):
                # 節流：佇列滿時先收割已完成的 Future
                while len(active_futures) >= MAX_PENDING:
                    done, _ = wait(active_futures, return_when=FIRST_COMPLETED)
                    for f in done:
                        active_futures.discard(f)
                        try:
                            results.append(f.result())
                            timer.task_completed(b_show_msg=True, bar=True)
                        except Exception as e:
                            timer.logger.log(f"Task failed: {e}", "ERROR")
                    if not done:
                        break

                active_futures.add(executor.submit(_throttled_task, i, obj.j_value))

        # 收尾：等待所有剩餘 Future
        while active_futures:
            done, active_futures = wait(active_futures, return_when=FIRST_COMPLETED)
            for f in done:
                try:
                    results.append(f.result())
                    timer.task_completed(b_show_msg=True, bar=True)
                except Exception as e:
                    timer.logger.log(f"Task failed: {e}", "ERROR")

        timer.stop()

    timer.show_info()
    assert len(results) == TOTAL, f"結果數量不匹配：{len(results)}/{TOTAL}"
    print(f"✅ 節流雙重迴圈驗證通過：收集到 {len(results):,}/{TOTAL:,} 筆結果")


# ---------------------------------------------------------------------------
# 補充測試：來自 legacy newTest.py 的「批次節流雙重迴圈」模式
# 外層每輪收集一個批次後再提交，呼叫 batched_task_completed()
# ---------------------------------------------------------------------------

def _batched_task(i_batch: list, j_value: int) -> list:
    """批次工作函式：一次處理多個 i，回傳 list[dict]"""
    results = []
    for i in i_batch:
        time.sleep(0.0005)
        results.append({"i": i, "j": j_value, "result": j_value * i})
    return results


def unit_test__multiprocess_batched_throttled():
    """
    批次節流雙重迴圈模式（對應 legacy newTest.py）。
    外層蒐集足夠的 i 後才提交一個批次 Future；使用 batched_task_completed() 更新進度。
    """
    OUTER_N = 5        # 外層迴圈（高成本物件）
    INNER_M = 200      # 內層迴圈（子任務）
    TOTAL = OUTER_N * INNER_M
    BATCH_SIZE = 50
    MAX_WORKERS = min(os.cpu_count() or 4, 4)
    MAX_PENDING = MAX_WORKERS * 2

    timer = MultiProcessLoopedFunctionTimer(
        total=TOTAL, inline=True, color="gray"
    )

    print(
        f"\n<<< 批次節流雙重迴圈測試 "
        f"(Workers={MAX_WORKERS}, Batch={BATCH_SIZE}, Total={TOTAL}) >>>"
    )

    results = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        active_futures: set = set()
        timer.start()

        for j in range(OUTER_N):
            obj = _HighCostObj(j)
            batch: list = []

            for i in range(INNER_M):
                batch.append(i)
                is_last = (i == INNER_M - 1)

                if len(batch) >= BATCH_SIZE or is_last:
                    # 節流：佇列滿時先收割
                    while len(active_futures) >= MAX_PENDING:
                        done, _ = wait(active_futures, return_when=FIRST_COMPLETED)
                        for f in done:
                            active_futures.discard(f)
                            try:
                                batch_result = f.result()
                                results.extend(batch_result)
                                timer.batched_task_completed(
                                    len(batch_result), b_show_msg=True, bar=True
                                )
                            except Exception as e:
                                timer.logger.log(f"Task failed: {e}", "ERROR")
                        if not done:
                            break

                    if batch:
                        active_futures.add(
                            executor.submit(_batched_task, batch, obj.j_value)
                        )
                        batch = []

        # 收尾
        while active_futures:
            done, active_futures = wait(active_futures, return_when=FIRST_COMPLETED)
            for f in done:
                try:
                    batch_result = f.result()
                    results.extend(batch_result)
                    timer.batched_task_completed(
                        len(batch_result), b_show_msg=True, bar=True
                    )
                except Exception as e:
                    timer.logger.log(f"Task failed: {e}", "ERROR")

        timer.stop()

    timer.show_info()
    assert len(results) == TOTAL, f"結果數量不匹配：{len(results)}/{TOTAL}"
    print(f"✅ 批次節流雙重迴圈驗證通過：收集到 {len(results):,}/{TOTAL:,} 筆結果")


if __name__ == "__main__":
    unit_test__single_thread()
    unit_test__decorator()
    unit_test__multiprocess()
    unit_test__multiprocess_throttled()
    unit_test__multiprocess_batched_throttled()
