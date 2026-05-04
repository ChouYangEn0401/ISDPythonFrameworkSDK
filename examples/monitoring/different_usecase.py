"""
different_usecase.py
====================
isd_py_framework_sdk.monitoring 五種使用情境的可執行範例。

直接執行：
    python examples/monitoring/different_usecase.py

情境一  單進程迴圈 ── 最基本的用法，逐一 start/stop 並顯示 inline 進度條。
情境二  裝飾器計時 ── 透過 @LoopedFunction_timer_decorator 自動計時 class method。
情境三  多工 as_completed ── ProcessPoolExecutor 任務無序完成，用 task_completed() 更新進度。
情境四  多工雙重迴圈（節流）── 外層高成本初始化 + 內層大量任務；
           透過 wait(FIRST_COMPLETED) 限制佇列深度，防止記憶體爆炸。
情境五  多工雙重迴圈（批次節流）── 同情境四，但先把內層任務打包成批次再提交，
           減少 pickling 次數並用 batched_task_completed() 一次更新多個進度。
"""
from concurrent.futures import ProcessPoolExecutor, as_completed, wait, FIRST_COMPLETED
import os
import time

from isd_py_framework_sdk.monitoring import (
    ColorLiteral,
    LoopedFunctionTimer,
    LoopedFunction_timer_decorator,
    MultiProcessLoopedFunctionTimer,
)

# ── 各情境使用不同顏色，方便在 terminal 上一眼區分 ──
COLOR_SINGLE_LOOP:        ColorLiteral = "yellow"
COLOR_DECORATOR:          ColorLiteral = "purple"
COLOR_MULTIPROC_SIMPLE:   ColorLiteral = "sky_blue"
COLOR_MULTIPROC_THROTTLE: ColorLiteral = "red"
COLOR_MULTIPROC_BATCH:    ColorLiteral = "gray"


# ===========================================================================
# 情境一：單進程迴圈
# ===========================================================================

def demo_single_loop__inline_progress_bar():
    """
    【情境一】單進程迴圈，手動呼叫 start/stop，示範：
    - inline 模式下 \\r 覆寫同行，不會跳行刷屏
    - 顏色填充（yellow）與 ░ 空格顯示
    - ETA 隨迭代收斂至 0
    - show_info() 印出總耗時與平均耗時摘要
    適用場景：任何單執行緒的「for 迴圈任務」進度監控。
    """
    total = 100
    timer = LoopedFunctionTimer(
        total=total,
        inline=True,
        level="CHECKPOINT",
        color=COLOR_SINGLE_LOOP,
    )

    print(f"<<< [情境一] 單進程迴圈 (total={total}) >>>")
    for i in range(total):
        timer.start()
        time.sleep(0.01)
        timer.stop()
        timer.msg(i + 1, bar=True)
    timer.show_info()


# ===========================================================================
# 情境二：裝飾器計時
# ===========================================================================

class _TimedMethodHost:
    """
    裝飾器示範用 host class。
    只需在 __init__ 設置 self.timer，裝飾器即可自動接管 start/stop/msg。
    """

    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.timer = LoopedFunctionTimer(total=total_tasks, color=COLOR_DECORATOR)

    @LoopedFunction_timer_decorator
    def fast_task(self, task_id: int) -> str:
        time.sleep(0.1)
        return f"fast/{task_id}"

    @LoopedFunction_timer_decorator
    def slow_task(self, task_id: int) -> str:
        time.sleep(0.5)
        return f"slow/{task_id}"

    def run_fast(self):
        self.timer.reset()
        for i in range(self.total_tasks):
            self.fast_task(i)
        self.timer.end_msg()

    def run_slow(self):
        self.timer.reset()
        for i in range(self.total_tasks):
            self.slow_task(i)
        self.timer.show_info()


def demo_decorator__auto_timer_on_class_method():
    """
    【情境二】@LoopedFunction_timer_decorator 自動計時 class method，示範：
    - 裝飾器正確讀取 self.timer，無需呼叫端手動 start/stop
    - timer.reset() 後可重複用於不同速度的任務（fast → slow）
    - end_msg() 與 show_info() 都能在迴圈結束後正常輸出
    適用場景：需要對某個物件的核心方法做逐次計時，但不想在每個呼叫點手動 start/stop。
    """
    print("\n<<< [情境二] 裝飾器計時 (fast × 20, slow × 20) >>>")
    host = _TimedMethodHost(total_tasks=20)
    host.run_fast()
    host.run_slow()


# ===========================================================================
# 情境三：多工 as_completed（簡單版）
# ===========================================================================

def _simple_worker(item_id: int) -> str:
    """子進程任務：模擬固定耗時工作（0.01s）。"""
    time.sleep(0.01)
    return f"done/{item_id}"


def demo_multiprocess__as_completed_simple():
    """
    【情境三】ProcessPoolExecutor + as_completed，示範：
    - 任務完成順序不固定，task_completed() 仍能正確累計計數
    - MultiProcessLoopedFunctionTimer 的內建節流機制（每 1%）不漏計
    - start() 在提交前、stop() 在 as_completed 結束後各呼叫一次
    適用場景：大量「等長、獨立、無序」任務的並行處理，是多工最常見的入門模式。
    """
    total = 10_000
    max_workers = os.cpu_count() or 4

    timer = MultiProcessLoopedFunctionTimer(
        total=total,
        inline=True,
        level="CHECKPOINT",
        color=COLOR_MULTIPROC_SIMPLE,
    )

    print(f"\n<<< [情境三] 多工 as_completed (workers={max_workers}, total={total}) >>>")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_simple_worker, i): i for i in range(total)}

        timer.start()
        for future in as_completed(futures):
            try:
                future.result()
                timer.task_completed(b_show_msg=True, bar=True)
            except Exception as e:
                timer.logger.log(f"Task failed: {e}", "ERROR")
        timer.stop()

    timer.show_info()


# ===========================================================================
# 情境四：多工雙重迴圈（逐一節流）
# ===========================================================================

class _ExpensiveInitObj:
    """
    模擬「外層迴圈每輪需高成本初始化」的物件。
    例如：從磁碟讀取設定、建立資料庫連線、載入子模型等。
    初始化後，內層的每次計算都是輕量級操作。
    """

    def __init__(self, group_id: int):
        # 在主進程初始化一次，子進程只接收可序列化的純資料
        self.group_id = group_id


def _single_item_worker(item_id: int, group_id: int) -> dict:
    """
    子進程工作函式：只接收可序列化的純資料，避免整個物件被 pickle。
    每次完成一個項目，對應 task_completed() 呼叫一次。
    """
    time.sleep(0.001)
    return {"group": group_id, "item": item_id, "result": group_id * item_id}


def demo_multiprocess__double_loop_throttled():
    """
    【情境四】雙重迴圈 + 逐一節流，示範：
    - 外層高成本物件只在主進程建立（OUTER_N 次），避免跨進程重複初始化
    - 內層以 wait(FIRST_COMPLETED) 節流，確保 active_futures 深度不超過 MAX_PENDING，
      防止過多 pickle 副本佔滿記憶體
    - task_completed() 在每個 Future 完成後呼叫，進度計數精確至個位
    適用場景：外層迴圈有高成本初始化（IO、模型載入），內層任務量遠大於 CPU 數的雙重迴圈。
    """
    OUTER_N     = 5    # 外層迴圈：高成本物件數量
    INNER_M     = 200  # 內層迴圈：每個物件對應的子任務數
    TOTAL       = OUTER_N * INNER_M
    MAX_WORKERS = min(os.cpu_count() or 4, 4)
    MAX_PENDING = MAX_WORKERS * 2  # 節流閾值：保持佇列不超過工作者數的 2 倍

    timer = MultiProcessLoopedFunctionTimer(
        total=TOTAL, inline=True, color=COLOR_MULTIPROC_THROTTLE
    )

    print(
        f"\n<<< [情境四] 雙重迴圈節流 "
        f"(outer={OUTER_N}, inner={INNER_M}, workers={MAX_WORKERS}, limit={MAX_PENDING}) >>>"
    )

    results = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        active_futures: set = set()
        timer.start()

        for j in range(OUTER_N):
            obj = _ExpensiveInitObj(j)

            for i in range(INNER_M):
                # 節流：佇列滿時先收割，避免 active_futures 無限增長
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

                active_futures.add(executor.submit(_single_item_worker, i, obj.group_id))

        # 收尾：等待所有尚未收割的 Future
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
    print(f"✅ [情境四] 完成：共處理 {len(results):,}/{TOTAL:,} 筆")


# ===========================================================================
# 情境五：多工雙重迴圈（批次節流）
# ===========================================================================

def _batch_worker(item_batch: list, group_id: int) -> list:
    """
    批次子進程工作函式：一次接收多個 item_id，回傳 list[dict]。
    將多個任務打包成一個 Future 提交，減少 pickle/IPC 次數。
    對應進度更新：batched_task_completed(len(batch_result))。
    """
    results = []
    for item_id in item_batch:
        time.sleep(0.0005)
        results.append({"group": group_id, "item": item_id, "result": group_id * item_id})
    return results


def demo_multiprocess__double_loop_batched_throttled():
    """
    【情境五】雙重迴圈 + 批次節流，示範：
    - 內層任務先累積到 BATCH_SIZE 後才一次提交一個 Future（減少 IPC overhead）
    - 仍以 wait(FIRST_COMPLETED) 節流，確保 active_futures 不爆炸
    - batched_task_completed(n) 一次更新 n 個進度，適合批次 Future 的計數場景
    適用場景：任務數量遠大於 CPU 數、且每個任務耗時很短時，
              打包批次能大幅降低 multiprocessing 的調度 overhead。
    """
    OUTER_N     = 5    # 外層迴圈：高成本物件數量
    INNER_M     = 200  # 內層迴圈：每個物件對應的子任務數
    TOTAL       = OUTER_N * INNER_M
    BATCH_SIZE  = 50   # 每個 Future 包含的子任務數（調高可降低 IPC 頻率）
    MAX_WORKERS = min(os.cpu_count() or 4, 4)
    MAX_PENDING = MAX_WORKERS * 2

    timer = MultiProcessLoopedFunctionTimer(
        total=TOTAL, inline=True, color=COLOR_MULTIPROC_BATCH
    )

    print(
        f"\n<<< [情境五] 雙重迴圈批次節流 "
        f"(outer={OUTER_N}, inner={INNER_M}, batch={BATCH_SIZE}, workers={MAX_WORKERS}) >>>"
    )

    results = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        active_futures: set = set()
        timer.start()

        for j in range(OUTER_N):
            obj = _ExpensiveInitObj(j)
            batch: list = []

            for i in range(INNER_M):
                batch.append(i)
                is_last_in_inner = (i == INNER_M - 1)

                if len(batch) >= BATCH_SIZE or is_last_in_inner:
                    # 節流：批次滿了要提交前，先確保佇列有空位
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
                            executor.submit(_batch_worker, batch, obj.group_id)
                        )
                        batch = []

        # 收尾：等待所有尚未收割的批次 Future
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
    print(f"✅ [情境五] 完成：共處理 {len(results):,}/{TOTAL:,} 筆")


# ===========================================================================
# 入口
# ===========================================================================

if __name__ == "__main__":
    demo_single_loop__inline_progress_bar()
    demo_decorator__auto_timer_on_class_method()
    demo_multiprocess__as_completed_simple()
    demo_multiprocess__double_loop_throttled()
    demo_multiprocess__double_loop_batched_throttled()
