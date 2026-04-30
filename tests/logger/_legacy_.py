import functools
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime
from statistics import mean
from typing import Optional, Union
import datetime
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.hyper_framework.monitor.logging.console import ConsoleLogger, ConsoleColorProvider
from src.hyper_framework.monitor.logging.base import ColorLoggerBase, ColorProvider

### --- 主物件 --- ###
class LoopedFunctionTimer:
    @property
    def count(self):
        return len(self._time_records)

    @property
    def last(self):
        return self._time_records[-1] if self._time_records else None

    @property
    def avg(self):
        return mean(self._time_records) if self._time_records else None

    @property
    def sum(self):
        return self._total_time

    def __init__(
        self,
        total: Optional[int] = None,
        inline: bool = True,
        color: ColorProvider.ColorLiteral = "reset",
        logger: Optional[ColorLoggerBase] = None,
    ):
        self._total = total
        self.reset()

        self._start_time = None
        self._time_records = []
        self._total_time = 0
        self._inline = inline
        self._color = color
        self._last_processed = 0

        self.logger = logger or ConsoleLogger()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    def reset_total(self, total: int):
        self._total = total

    def reset(self):
        self._start_time = None
        self._time_records = []
        self._total_time = 0

    def start(self):
        self._start_time = time.perf_counter()

    def stop(self):
        if self._start_time is None:
            raise RuntimeError("Timer not started.")
        elapsed = time.perf_counter() - self._start_time
        self._time_records.append(elapsed)
        self._total_time += elapsed
        self._start_time = None
        return elapsed

    def restart(self, b_do_reset: bool = False):
        self.stop()
        if b_do_reset:
            self.reset()
        self.start()

    def eta(self, processed: int, total: Optional[int] = None, b_accurate=False):
        """Estimate time for remaining tasks"""
        if processed == 0 or not self._time_records:
            return None

        total = total if total is not None else self._total
        if total is None:
            return None

        avg_per_item = self.avg
        remaining = total - processed
        if remaining <= 0 or avg_per_item is None:
            return 0.0

        remaining_time = remaining * avg_per_item
        if b_accurate and self._start_time:
            remaining_time -= (time.perf_counter() - self._start_time)

        return remaining_time

    def msg(
        self,
        processed: int,
        total: Optional[int] = None,
        inline: Optional[bool] = None,
        bar: bool = False,
        bar_len: int = 30,
        color: Optional[ColorProvider.ColorLiteral] = None,
    ):
        total = total or self._total
        inline = self._inline if inline is None else inline

        if not total:
            raise ValueError("Total is required for progress bar.")

        # 計算 ETA
        eta_val = self.eta(processed, total)
        eta_str = (
            f"{eta_val:.3f}s ({str(datetime.timedelta(seconds=int(eta_val))).replace(' days, ', ':')})"
            if eta_val is not None
            else "N/A"
        )

        # 取得顏色代碼
        active_color = color or self._color or "reset"
        if self.logger.color_provider:
            fg_code = self.logger.color_provider.get_color_code(active_color)
            gray_code = self.logger.color_provider.get_color_code("gray")
            reset_code = self.logger.color_provider.get_color_code("reset")
        else:
            fg_code = gray_code = reset_code = ""

        # 繪製進度條或普通訊息
        if bar:
            ratio = min(max(processed / total, 0), 1)
            filled_len = int(bar_len * ratio)
            bar_str = f"{fg_code}{'█' * filled_len}{gray_code}{'░' * (bar_len - filled_len)}{reset_code}"
            text = f"[{bar_str}] {processed:>3,}/{total:<3,} TRT={self._total_time:.3f}s ETA={eta_str}"
        else:
            text = f"Progress: {processed:12.0f}/{total}, TRT={self._total_time:.3f}s, ETA={eta_str}"

        # 輸出（inline 或換行）
        if inline:
            self.logger.overwrite(text, color=active_color)
        else:
            self.logger.write(text, color=active_color)

    def last_msg(
        self,
        inline: Optional[bool] = None,
        bar: bool = False,
        bar_len: int = 30,
        color: Optional[ColorProvider.ColorLiteral] = None,
    ):
        """輸出最終進度條"""
        active_color = color or self._color
        self.msg(self._total, self._total, inline, bar, bar_len, active_color)

    def end_msg(self):
        self.logger.write("\n✅ DONE !!", color=self._color or "green")

    def show_info(
            self,
            color: Optional[ColorProvider.ColorLiteral] = "reset",
            b_clean_progress_bar = False
    ):
        """顯示任務總結資訊"""
        active_color = color or self._color

        if b_clean_progress_bar:
            self.logger.overwrite(" " * 100, color=active_color)

        if self.avg:
            msg = (
                f"\n✅ 所有任務完成！\n\t總任務： {self._total}, "
                f"總耗時: {self.sum:.3f}s, 平均單次耗時: {self.avg:.3f}s"
            )
        else:
            msg = (
                f"\n✅ 所有任務完成！\n\t總任務： {self._total}, "
                f"總耗時: {self.sum:.3f}s, 平均單次耗時: N/A"
            )

        self.logger.write(msg, color=active_color)
        self.logger.write("-" * 50, color=active_color)
        self.logger.flush()  # 在整個程序結束前，再次清空輸出緩衝區

### --- 主物件(多工專用) --- ###
class MultiProcessLoopedFunctionTimer(LoopedFunctionTimer):
    """
        專為多工 (Multiprocessing) 設計的計時器。
        它只計算總運行時間，並根據已完成的任務數來估算平均時間和 ETA。
    """

    def __init__(
            self, total: int = None,
            inline: bool = True,
            color: str = "reset",
            logger: Optional[ColorLoggerBase] = None,
    ):
        super().__init__(total, inline, color, logger)
        self._processed_count = 0
        # 設置更新閾值 (為了性能，我們保留這個機制)
        self._last_update_count = 0
        self.update_interval = max(1, min(int(self._total * 0.01) if self._total else 10000, 10000))

    def batched_task_completed(self, batch_size, b_show_msg: bool = True, **kwargs):
        """
            供主程式呼叫的介面：通知計時器一個批次任務已完成。
            它將在內部管理多工計時邏輯。
        """
        self._processed_count += batch_size

        # 檢查是否達到更新閾值
        if (
            self._processed_count - self._last_update_count < self.update_interval
            and self._processed_count != self._total
        ):
            return

        self._last_update_count = self._processed_count

        # 1. 計算總運行時間
        # 由於只有 start() 在最開始被呼叫一次，這裡計算的是從開始到現在的總耗時
        if self._start_time is not None:
            current_total_time = time.perf_counter() - self._start_time
        else:
            current_total_time = 0

        # 2. 更新總運行時間 (self.sum)
        self._total_time = current_total_time

        # 3. 更新平均單次耗時 (self.avg)
        if self._processed_count > 0:
            # 多工環境下的平均耗時 = 總運行時間 / 已完成任務數
            # 只需要在 _time_records 列表中放一個元素，讓 self.avg 屬性正確計算即可
            avg_item_time = current_total_time / self._processed_count
            self._time_records = [avg_item_time]
        else:
            self._time_records = []

        # 4. 顯示進度
        if b_show_msg:
            # 使用父類的 msg 方法顯示進度
            self.msg(self._processed_count, total=self._total, **kwargs)

    def task_completed(self, b_show_msg: bool = True, **kwargs):
        self.batched_task_completed(1, b_show_msg, **kwargs)

    def stop(self):
        """覆寫 stop()，僅用來記錄最終總時間"""
        if self._start_time is None:
            return None
        elapsed = time.perf_counter() - self._start_time
        self._total_time = elapsed
        self._start_time = None
        # 最後一次更新平均值
        if self._processed_count > 0:
            avg_item_time = elapsed / self._processed_count
            self._time_records = [avg_item_time]
        return elapsed

### --- 主物件(裝飾器) --- ###
def LoopedFunction_timer_decorator(func=None, *, timer: "LoopedFunctionTimer"=None):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            t = None
            if args and hasattr(args[0], 'timer'):
                t = args[0].timer
            elif timer:
                t = timer
            else:
                raise ValueError("No timer found for this function")

            t.start()
            result = f(*args, **kwargs)
            t.stop()
            t.msg(t.count, bar=True)
            return result

        return wrapper

    if func:
        return decorator(func)
    return decorator
""" 【 使用範例 】 ---------------------------------------------

# 裝飾 class method
class A:
    def __init__(self):
        self.timer = LoopTimer(total=3)

    @LoopedFunction_timer_decorator
    def method(self, x):
        import time; time.sleep(0.2)
        return x + 1

# 裝飾普通函數
t = LoopTimer(total=3)

@LoopedFunction_timer_decorator(timer=t)
def func(x):
    import time; time.sleep(0.2)
    return x * 2

--------------------------------------------- 【 使用範例 】"""

### --- 各種單元測試 --- ###
def unit_test__single_thread():
    total = 100
    timer = LoopedFunctionTimer(total=total, inline=True, color='yellow')

    print(f"<<< 啟動 LoopTimer 單進程任務 (Total Tasks: {total}) >>>")
    for i in range(total):
        timer.start()
        time.sleep(0.01)
        timer.stop()
        timer.msg(i + 1, bar=True)  # 顯示進度條
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
    """模擬一個耗時不均勻的任務"""
    # sleep_time = random.uniform(0.05, 0.25)
    sleep_time = 0.01
    time.sleep(sleep_time)
    return f"Processed item {data_item} in {sleep_time:.2f}s"
def unit_test__multiprocess():
    # 1. 設定參數
    TOTAL_ITEMS = 10000
    MAX_WORKERS = os.cpu_count() or 4
    # 2. 初始化計時器
    multi_timer = MultiProcessLoopedFunctionTimer(total=TOTAL_ITEMS, inline=True, color='cyan')

    # 3. 使用 ProcessPoolExecutor 實作動態調度
    print(f"<<< 啟動 MultiLoopTimer 多工進度條 (Workers: {MAX_WORKERS}, Total Tasks: {TOTAL_ITEMS}) >>>")
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 3.1. 提交所有任務 (Producer/生產者) # executor.submit() 會返回 Future 物件
        futures = {executor.submit(_heavy_task, i): i for i in range(TOTAL_ITEMS)}

        # 3.2. 使用 as_completed 動態收集結果 (Consumer/消費者) # as_completed 會依據任務完成的順序返回 Future 物件，而不是提交的順序
        multi_timer.start()
        for future in as_completed(futures):
            try:
                m_result = future.result()  # 獲取任務結果，這一步是同步的 (相當於 'wait join' 或 'async 等候任務完成')
                multi_timer.task_completed(b_show_msg=True, bar=True)
            except Exception as e:
                print(f"\n[Error] Task failed: {e}")
        multi_timer.stop()

    # 4. 輸出最終結果
    multi_timer.show_info()


if __name__ == "__main__":
    unit_test__single_thread()
    unit_test__decorator()
    unit_test__multiprocess()

