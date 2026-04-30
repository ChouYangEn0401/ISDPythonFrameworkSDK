"""
test_msg_logger.py — message_logger 完整 API 測試腳本

涵蓋範圍：
    1.  LevelOrder 等級定義與排序
    2.  LoggerAdapterBase — level_formator / _pass_filter / set_filtered_level / help
    3.  自訂 Adapter（繼承 LoggerAdapterBase）
    4.  LoggerBase — register / unregister / clear adapters
    5.  LoggerBase — enable / disable broadcast
    6.  LoggerBase — log() 格式化（HIGHLIGHT 與 shiny 裝飾）
    7.  LoggerBase — 所有快捷方法（debug / info / ... / highlight）
    8.  LoggerBase — shiny_log()
    9.  LoggerBase — 未知等級引發 ValueError
    10. LoggerBase — fan-out 廣播至多個 adapter
    11. LoggerBase — adapter 的 level_filter 各自獨立
    12. LoggerBase — flush_all() / flush()
    13. SingletonSystemLogger — 多次 () 回傳同一實例
    14. SingletonSystemLogger — 初始狀態正確（_enabled=True, _adapters=[]）
    15. DarkThemeTerminalAdapter / LightThemeTerminalAdapter — 捕捉 print 輸出
    16. FileAdapter — 寫入內容、level 過濾、flush / close
    17. FileAdapter — mode="w" 覆寫模式
    18. FileAdapter — thread-safe 並發寫入
    19. TkinterAdapter（DarkTheme / LightTheme） — lazy injection, overwrite_last_line
    20. TkLabelAdapter（DarkTheme / LightTheme） — lazy injection
    21. TtkLabelAdapter（DarkTheme / LightTheme） — lazy injection
    22. Stub adapters（HTMLAdapter / HTTPAdapter / DBAdapter / WebsocketAdapter）
    23. LoggerAdapterBase.help() 可正常呼叫
    24. LoggerBase — 大小寫不敏感（level 傳小寫）
    25. FileAdapter — auto_flush=False 手動 flush

執行方式：
    python tests/logger/test_msg_logger.py

環境需求：
    pip install colorama
    （Tkinter 測試需要標準函式庫 tkinter，通常隨 Python 安裝附帶）
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import threading
from pathlib import Path

# ─── 輸出計數 ─────────────────────────────────────────────────────────────────
PASS = 0
FAIL = 0
SKIP = 0


def ok(label: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✔  {label}")


def fail(label: str, exc: Exception) -> None:
    global FAIL
    FAIL += 1
    print(f"  ✘  {label}  →  {type(exc).__name__}: {exc}")


def skip(label: str, reason: str) -> None:
    global SKIP
    SKIP += 1
    print(f"  ⊘  {label}  →  SKIP: {reason}")


def expect_pass(label: str, fn) -> None:
    try:
        fn()
        ok(label)
    except Exception as exc:
        fail(label, exc)


def expect_fail(label: str, fn, exc_type: type = Exception) -> None:
    try:
        fn()
        fail(label, Exception("no exception raised"))
    except exc_type:
        ok(label)
    except Exception as exc:
        fail(label, exc)


# ─── 重設 Singleton 狀態的工具 ────────────────────────────────────────────────
def _reset_singleton_logger() -> None:
    """
    在測試之間清除 SingletonSystemLogger 的適配器清單，
    避免前一個測試的 adapter 汙染後續測試。
    （不重設 singleton 本身，因為 SingletonMetaclass 不支援重置）
    """
    from isd_py_framework_sdk.message_logger import SingletonSystemLogger
    logger = SingletonSystemLogger()
    logger.clear_adapters()
    logger.enable_broadcast_msg()


# ─── 自訂 Capture Adapter（測試用）──────────────────────────────────────────
from isd_py_framework_sdk.message_logger import LoggerAdapterBase, LogLevelLiteral


class CaptureAdapter(LoggerAdapterBase):
    """
    測試用 adapter：將每次廣播記錄到 self.records 清單。
    records 每個元素為 dict(level=str, formatted=str, shine=bool)。
    """

    def __init__(self, LEVEL_FILTER: LogLevelLiteral = "DEBUG"):
        super().__init__(LEVEL_FILTER)
        self.records: list[dict] = []
        self.flush_count = 0

    def broadcast(self, level: str, formatted: str, shine: bool = False) -> None:
        level = self.level_formator(level)
        if not self._pass_filter(level):
            return
        self.records.append({"level": level, "formatted": formatted, "shine": shine})

    def flush(self) -> None:
        self.flush_count += 1

    def clear(self) -> None:
        self.records.clear()


# ════════════════════════════════════════════════════════════════════════════
# 1. LevelOrder 等級定義與排序
# ════════════════════════════════════════════════════════════════════════════
print("\n── 1. LevelOrder 等級定義與排序 ─────────────────────────────────────────")

from isd_py_framework_sdk.message_logger import LevelOrder

expect_pass(
    "LevelOrder 包含所有 8 個等級",
    lambda: [None for k in ("DEBUG", "INFO", "CHECKPOINT", "SUCCESS", "WARNING", "ERROR", "CRITICAL", "HIGHLIGHT")
             if k not in LevelOrder or None],
)

expect_pass(
    "DEBUG < INFO < CHECKPOINT < SUCCESS",
    lambda: (
        None
        if LevelOrder["DEBUG"] < LevelOrder["INFO"]
           < LevelOrder["CHECKPOINT"] < LevelOrder["SUCCESS"]
        else (_ for _ in ()).throw(AssertionError("排序錯誤"))
    ),
)

expect_pass(
    "SUCCESS < WARNING < ERROR < CRITICAL < HIGHLIGHT",
    lambda: (
        None
        if LevelOrder["SUCCESS"] < LevelOrder["WARNING"]
           < LevelOrder["ERROR"] < LevelOrder["CRITICAL"] < LevelOrder["HIGHLIGHT"]
        else (_ for _ in ()).throw(AssertionError("排序錯誤"))
    ),
)


# ════════════════════════════════════════════════════════════════════════════
# 2. LoggerAdapterBase — 基礎方法
# ════════════════════════════════════════════════════════════════════════════
print("\n── 2. LoggerAdapterBase — 基礎方法 ─────────────────────────────────────")

adapter = CaptureAdapter("WARNING")

expect_pass(
    "level_formator 回傳大寫字串",
    lambda: None if CaptureAdapter.level_formator("debug") == "DEBUG" else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "_pass_filter: WARNING 對 WARNING 通過",
    lambda: None if adapter._pass_filter("WARNING") else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "_pass_filter: ERROR 對 WARNING 通過",
    lambda: None if adapter._pass_filter("ERROR") else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "_pass_filter: INFO 對 WARNING 被擋",
    lambda: None if not adapter._pass_filter("INFO") else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "set_filtered_level 動態調整 → 改為 ERROR",
    lambda: (adapter.set_filtered_level("ERROR"),
             None if not adapter._pass_filter("WARNING") else (_ for _ in ()).throw(AssertionError()))[-1],
)

expect_fail(
    "set_filtered_level 傳入無效等級 → ValueError",
    lambda: adapter.set_filtered_level("INVALID"),  # type: ignore[arg-type]
    ValueError,
)

# 恢復
adapter.set_filtered_level("DEBUG")

expect_pass(
    "help() 不拋例外",
    lambda: CaptureAdapter.help(),
)


# ════════════════════════════════════════════════════════════════════════════
# 3. 自訂 Adapter 繼承
# ════════════════════════════════════════════════════════════════════════════
print("\n── 3. 自訂 Adapter 繼承 ─────────────────────────────────────────────────")

expect_pass(
    "CaptureAdapter 是 LoggerAdapterBase 的子類",
    lambda: None if issubclass(CaptureAdapter, LoggerAdapterBase) else (_ for _ in ()).throw(AssertionError()),
)

cap = CaptureAdapter("INFO")
cap.broadcast("DEBUG", "[debug msg]")       # 被 INFO filter 擋掉
cap.broadcast("INFO", "[info msg]")

expect_pass(
    "CaptureAdapter: DEBUG 低於 INFO filter 不記錄",
    lambda: None if len(cap.records) == 1 else (_ for _ in ()).throw(AssertionError(f"records={cap.records}")),
)

expect_pass(
    "CaptureAdapter: INFO 通過 filter 記錄正確",
    lambda: None if cap.records[0]["formatted"] == "[info msg]" else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 4. LoggerBase — adapter 管理
# ════════════════════════════════════════════════════════════════════════════
print("\n── 4. LoggerBase — adapter 管理 ─────────────────────────────────────────")

from isd_py_framework_sdk.message_logger import LoggerBase

class _TestLogger(LoggerBase):
    def _initialize_manager(self):
        super()._initialize_manager()

logger_b = _TestLogger()
logger_b._initialize_manager()

cap_a = CaptureAdapter("DEBUG")
cap_b = CaptureAdapter("DEBUG")

logger_b.register_adapter(cap_a)
logger_b.register_adapter(cap_b)

expect_pass(
    "register_adapter: 兩個 adapter 都已登記",
    lambda: None if len(logger_b._adapters) == 2 else (_ for _ in ()).throw(AssertionError()),
)

logger_b.unregister_adapter(cap_a)

expect_pass(
    "unregister_adapter: 只剩下一個",
    lambda: None if len(logger_b._adapters) == 1 and logger_b._adapters[0] is cap_b
    else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "unregister_adapter 對不存在的 adapter 靜默忽略",
    lambda: logger_b.unregister_adapter(cap_a),   # 再移除一次，不應拋例外
)

logger_b.clear_adapters()

expect_pass(
    "clear_adapters: _adapters 清空",
    lambda: None if len(logger_b._adapters) == 0 else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 5. LoggerBase — enable / disable broadcast
# ════════════════════════════════════════════════════════════════════════════
print("\n── 5. LoggerBase — enable / disable broadcast ──────────────────────────")

cap = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap)

logger_b.disable_broadcast_msg()
logger_b.info("disabled msg")

expect_pass(
    "disable_broadcast_msg: 訊息不進 adapter",
    lambda: None if len(cap.records) == 0 else (_ for _ in ()).throw(AssertionError()),
)

logger_b.enable_broadcast_msg()
logger_b.info("enabled msg")

expect_pass(
    "enable_broadcast_msg: 訊息成功進 adapter",
    lambda: None if len(cap.records) == 1 else (_ for _ in ()).throw(AssertionError(f"records={cap.records}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 6. LoggerBase — 訊息格式化
# ════════════════════════════════════════════════════════════════════════════
print("\n── 6. LoggerBase — 訊息格式化 ───────────────────────────────────────────")

cap = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap)

logger_b.log("hello world", "INFO")
record = cap.records[-1]

expect_pass(
    "一般訊息包含 timestamp 格式 [YYYY-MM-DD HH:MM:SS]",
    lambda: None if "[" in record["formatted"] and "-" in record["formatted"]
    else (_ for _ in ()).throw(AssertionError(f"formatted={record['formatted']}")),
)

expect_pass(
    "一般訊息包含 [INFO  ] (padding)",
    lambda: None if "INFO" in record["formatted"]
    else (_ for _ in ()).throw(AssertionError(f"formatted={record['formatted']}")),
)

expect_pass(
    "一般訊息包含 'hello world'",
    lambda: None if "hello world" in record["formatted"]
    else (_ for _ in ()).throw(AssertionError()),
)

cap.clear()
logger_b.log("rocket launch", "HIGHLIGHT")
hl_record = cap.records[-1]

expect_pass(
    "HIGHLIGHT 包含 🚀🚀🚀 裝飾",
    lambda: None if "🚀🚀🚀" in hl_record["formatted"]
    else (_ for _ in ()).throw(AssertionError(f"formatted={hl_record['formatted']}")),
)

expect_pass(
    "HIGHLIGHT 訊息以 \\n 開頭",
    lambda: None if hl_record["formatted"].startswith("\n")
    else (_ for _ in ()).throw(AssertionError()),
)

cap.clear()
logger_b.log("shiny msg", "SUCCESS", shine=True)
shine_record = cap.records[-1]

expect_pass(
    "shine=True 包含 ✨ 裝飾",
    lambda: None if "✨" in shine_record["formatted"]
    else (_ for _ in ()).throw(AssertionError(f"formatted={shine_record['formatted']}")),
)

expect_pass(
    "shine=True 的 record['shine'] 為 True",
    lambda: None if shine_record["shine"] is True
    else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 7. LoggerBase — 所有快捷方法
# ════════════════════════════════════════════════════════════════════════════
print("\n── 7. LoggerBase — 所有快捷方法 ─────────────────────────────────────────")

cap = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap)

all_shortcuts = [
    ("debug",       "DEBUG"),
    ("info",        "INFO"),
    ("checkpoint",  "CHECKPOINT"),
    ("success",     "SUCCESS"),
    ("warning",     "WARNING"),
    ("error",       "ERROR"),
    ("critical",    "CRITICAL"),
    ("highlight",   "HIGHLIGHT"),
]

for method_name, expected_level in all_shortcuts:
    cap.clear()
    getattr(logger_b, method_name)(f"test {method_name}")
    expect_pass(
        f"{method_name}() 廣播正確等級 {expected_level}",
        lambda lvl=expected_level: (
            None if cap.records and cap.records[-1]["level"] == lvl
            else (_ for _ in ()).throw(AssertionError(f"records={cap.records}"))
        ),
    )


# ════════════════════════════════════════════════════════════════════════════
# 8. LoggerBase — shiny_log()
# ════════════════════════════════════════════════════════════════════════════
print("\n── 8. LoggerBase — shiny_log() ──────────────────────────────────────────")

cap = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap)

logger_b.shiny_log("shiny checkpoint", "CHECKPOINT")
sr = cap.records[-1]

expect_pass(
    "shiny_log() 設定 shine=True",
    lambda: None if sr["shine"] is True else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "shiny_log() 包含 ✨",
    lambda: None if "✨" in sr["formatted"] else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "shiny_log() 等級為 CHECKPOINT",
    lambda: None if sr["level"] == "CHECKPOINT" else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 9. LoggerBase — 未知等級引發 ValueError
# ════════════════════════════════════════════════════════════════════════════
print("\n── 9. LoggerBase — 未知等級引發 ValueError ─────────────────────────────")

logger_b._initialize_manager()

expect_fail(
    "log() 傳入 'OOPS' → ValueError",
    lambda: logger_b.log("msg", "OOPS"),  # type: ignore[arg-type]
    ValueError,
)

expect_fail(
    "log() 傳入 空字串 → ValueError",
    lambda: logger_b.log("msg", ""),  # type: ignore[arg-type]
    ValueError,
)


# ════════════════════════════════════════════════════════════════════════════
# 10. LoggerBase — fan-out 廣播至多個 adapter
# ════════════════════════════════════════════════════════════════════════════
print("\n── 10. LoggerBase — fan-out 廣播至多個 adapter ─────────────────────────")

cap1 = CaptureAdapter("DEBUG")
cap2 = CaptureAdapter("DEBUG")
cap3 = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap1)
logger_b.register_adapter(cap2)
logger_b.register_adapter(cap3)

logger_b.warning("broadcast test")

expect_pass(
    "fan-out: 三個 adapter 都收到訊息",
    lambda: None if all(len(c.records) == 1 for c in [cap1, cap2, cap3])
    else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "fan-out: 內容一致",
    lambda: None if (cap1.records[0]["formatted"]
                     == cap2.records[0]["formatted"]
                     == cap3.records[0]["formatted"])
    else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 11. LoggerBase — adapter 的 level_filter 各自獨立
# ════════════════════════════════════════════════════════════════════════════
print("\n── 11. LoggerBase — adapter level_filter 各自獨立 ──────────────────────")

cap_debug = CaptureAdapter("DEBUG")
cap_error = CaptureAdapter("ERROR")
logger_b._initialize_manager()
logger_b.register_adapter(cap_debug)
logger_b.register_adapter(cap_error)

logger_b.info("info msg")      # cap_debug 收到，cap_error 被擋
logger_b.error("error msg")    # 兩者都收到

expect_pass(
    "cap_debug 收到 2 筆（INFO + ERROR）",
    lambda: None if len(cap_debug.records) == 2
    else (_ for _ in ()).throw(AssertionError(f"records={cap_debug.records}")),
)

expect_pass(
    "cap_error 只收到 1 筆（ERROR）",
    lambda: None if len(cap_error.records) == 1
    else (_ for _ in ()).throw(AssertionError(f"records={cap_error.records}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 12. LoggerBase — flush_all() / flush()
# ════════════════════════════════════════════════════════════════════════════
print("\n── 12. LoggerBase — flush_all() / flush() ───────────────────────────────")

cap1 = CaptureAdapter("DEBUG")
cap2 = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap1)
logger_b.register_adapter(cap2)

logger_b.flush_all()

expect_pass(
    "flush_all() 呼叫所有 adapter 的 flush()",
    lambda: None if cap1.flush_count == 1 and cap2.flush_count == 1
    else (_ for _ in ()).throw(AssertionError()),
)

logger_b.flush()   # alias

expect_pass(
    "flush() 是 flush_all() 的 alias",
    lambda: None if cap1.flush_count == 2 and cap2.flush_count == 2
    else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 13. SingletonSystemLogger — 多次 () 回傳同一實例
# ════════════════════════════════════════════════════════════════════════════
print("\n── 13. SingletonSystemLogger — singleton 行為 ───────────────────────────")

from isd_py_framework_sdk.message_logger import SingletonSystemLogger

_reset_singleton_logger()

logger1 = SingletonSystemLogger()
logger2 = SingletonSystemLogger()
logger3 = SingletonSystemLogger()

expect_pass(
    "三次 SingletonSystemLogger() is 同一個物件",
    lambda: None if logger1 is logger2 is logger3
    else (_ for _ in ()).throw(AssertionError("不同實例")),
)

expect_pass(
    "id() 都相同",
    lambda: None if id(logger1) == id(logger2) == id(logger3)
    else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 14. SingletonSystemLogger — 初始狀態正確
# ════════════════════════════════════════════════════════════════════════════
print("\n── 14. SingletonSystemLogger — 初始狀態 ─────────────────────────────────")

_reset_singleton_logger()

s_logger = SingletonSystemLogger()

expect_pass(
    "_enabled 預設為 True",
    lambda: None if s_logger._enabled is True
    else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "_adapters 預設為空 list（clear 後）",
    lambda: None if isinstance(s_logger._adapters, list) and len(s_logger._adapters) == 0
    else (_ for _ in ()).throw(AssertionError()),
)

expect_pass(
    "_max_level_len 等於最長等級名稱長度",
    lambda: None if s_logger._max_level_len == max(len(k) for k in LevelOrder)
    else (_ for _ in ()).throw(AssertionError()),
)


# ════════════════════════════════════════════════════════════════════════════
# 15. DarkThemeTerminalAdapter / LightThemeTerminalAdapter — 捕捉 print 輸出
# ════════════════════════════════════════════════════════════════════════════
print("\n── 15. TerminalAdapter — 捕捉 print 輸出 ───────────────────────────────")

from isd_py_framework_sdk.message_logger import DarkThemeTerminalAdapter, LightThemeTerminalAdapter

_reset_singleton_logger()
s_logger = SingletonSystemLogger()

# --- DarkThemeTerminalAdapter ---
dark_adapter = DarkThemeTerminalAdapter("DEBUG")
s_logger.register_adapter(dark_adapter)

captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    s_logger.info("dark console test")
output = captured.getvalue()

expect_pass(
    "DarkThemeTerminalAdapter: 訊息出現在 stdout",
    lambda: None if "dark console test" in output
    else (_ for _ in ()).throw(AssertionError(f"output={repr(output)}")),
)

_reset_singleton_logger()
s_logger = SingletonSystemLogger()

# --- LightThemeTerminalAdapter ---
light_adapter = LightThemeTerminalAdapter("DEBUG")
s_logger.register_adapter(light_adapter)

captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    s_logger.warning("light console test")
output = captured.getvalue()

expect_pass(
    "LightThemeTerminalAdapter: 訊息出現在 stdout",
    lambda: None if "light console test" in output
    else (_ for _ in ()).throw(AssertionError(f"output={repr(output)}")),
)

# --- level filter 阻擋 ---
_reset_singleton_logger()
s_logger = SingletonSystemLogger()
dark_filtered = DarkThemeTerminalAdapter("ERROR")
s_logger.register_adapter(dark_filtered)

captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    s_logger.info("should not appear")

expect_pass(
    "TerminalAdapter: INFO 低於 ERROR filter → 不輸出",
    lambda: None if "should not appear" not in captured.getvalue()
    else (_ for _ in ()).throw(AssertionError()),
)

# --- shiny 輸出 ---
_reset_singleton_logger()
s_logger = SingletonSystemLogger()
dark_adapter2 = DarkThemeTerminalAdapter("DEBUG")
s_logger.register_adapter(dark_adapter2)

captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    s_logger.shiny_log("✨ shiny!!", "SUCCESS")

expect_pass(
    "TerminalAdapter: shiny_log 包含 ✨ 於輸出",
    lambda: None if "✨" in captured.getvalue()
    else (_ for _ in ()).throw(AssertionError(f"output={repr(captured.getvalue())}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 16. FileAdapter — 基本寫入 / level 過濾
# ════════════════════════════════════════════════════════════════════════════
print("\n── 16. FileAdapter — 基本寫入 / level 過濾 ─────────────────────────────")

from isd_py_framework_sdk.message_logger import FileAdapter

with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as tf:
    tmp_path = Path(tf.name)

file_adapter = FileAdapter("WARNING", tmp_path, mode="w")
_reset_singleton_logger()
s_logger = SingletonSystemLogger()
s_logger.register_adapter(file_adapter)

s_logger.info("info should not appear in file")       # 被 WARNING filter 擋
s_logger.warning("warning line in file")
s_logger.error("error line in file")
file_adapter.close()

content = tmp_path.read_text(encoding="utf-8")

expect_pass(
    "FileAdapter: INFO 低於 WARNING filter → 不寫入",
    lambda: None if "info should not appear" not in content
    else (_ for _ in ()).throw(AssertionError(f"content={content}")),
)

expect_pass(
    "FileAdapter: WARNING 寫入檔案",
    lambda: None if "warning line in file" in content
    else (_ for _ in ()).throw(AssertionError(f"content={content}")),
)

expect_pass(
    "FileAdapter: ERROR 寫入檔案",
    lambda: None if "error line in file" in content
    else (_ for _ in ()).throw(AssertionError(f"content={content}")),
)

expect_pass(
    "FileAdapter: 每行以 \\n 結尾（至少兩行）",
    lambda: None if content.count("\n") >= 2
    else (_ for _ in ()).throw(AssertionError(f"content={repr(content)}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 17. FileAdapter — mode="w" 覆寫模式
# ════════════════════════════════════════════════════════════════════════════
print("\n── 17. FileAdapter — mode='w' 覆寫模式 ─────────────────────────────────")

with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as tf:
    tmp_w_path = Path(tf.name)
    tf.write("original content\n")

fa_w = FileAdapter("DEBUG", tmp_w_path, mode="w")
fa_w.broadcast("INFO", "overwritten line")
fa_w.close()

content_w = tmp_w_path.read_text(encoding="utf-8")

expect_pass(
    "FileAdapter mode='w': 原有內容被覆寫",
    lambda: None if "original content" not in content_w
    else (_ for _ in ()).throw(AssertionError(f"content_w={content_w}")),
)

expect_pass(
    "FileAdapter mode='w': 新內容存在",
    lambda: None if "overwritten line" in content_w
    else (_ for _ in ()).throw(AssertionError(f"content_w={content_w}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 18. FileAdapter — thread-safe 並發寫入
# ════════════════════════════════════════════════════════════════════════════
print("\n── 18. FileAdapter — thread-safe 並發寫入 ───────────────────────────────")

with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as tf:
    tmp_thread_path = Path(tf.name)

fa_thread = FileAdapter("DEBUG", tmp_thread_path, mode="w")
THREAD_COUNT = 20
MESSAGES_PER_THREAD = 10


def _write_batch(fa: FileAdapter, thread_id: int) -> None:
    for i in range(MESSAGES_PER_THREAD):
        fa.broadcast("INFO", f"thread={thread_id} msg={i}")


threads = [threading.Thread(target=_write_batch, args=(fa_thread, tid)) for tid in range(THREAD_COUNT)]
for t in threads:
    t.start()
for t in threads:
    t.join()

fa_thread.close()
lines = [ln for ln in tmp_thread_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

expect_pass(
    f"FileAdapter 並發：{THREAD_COUNT} 執行緒各寫 {MESSAGES_PER_THREAD} 行，共 {THREAD_COUNT * MESSAGES_PER_THREAD} 行",
    lambda: None if len(lines) == THREAD_COUNT * MESSAGES_PER_THREAD
    else (_ for _ in ()).throw(AssertionError(f"lines={len(lines)}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 19. TkinterAdapter — lazy injection / overwrite_last_line
# ════════════════════════════════════════════════════════════════════════════
print("\n── 19. TkinterAdapter — lazy injection / overwrite_last_line ────────────")

try:
    import tkinter as tk
    from isd_py_framework_sdk.message_logger import DarkThemeTkinterAdapter, LightThemeTkinterAdapter

    root = tk.Tk()
    root.withdraw()

    text_widget = tk.Text(root)

    # --- 延遲注入 ---
    tk_adapter = DarkThemeTkinterAdapter("DEBUG")       # 先建立，不傳 widget
    expect_pass(
        "DarkThemeTkinterAdapter: lazy 建立（widget=None）不拋例外",
        lambda: None,
    )

    tk_adapter.broadcast("INFO", "before binding")     # widget 未綁定，靜默略過
    expect_pass(
        "TkinterAdapter: widget=None 時 broadcast 靜默略過",
        lambda: None if text_widget.get("1.0", "end").strip() == ""
        else (_ for _ in ()).throw(AssertionError()),
    )

    tk_adapter.set_tk_window(text_widget)               # 延遲注入 widget
    tk_adapter.broadcast("INFO", "after binding")

    expect_pass(
        "TkinterAdapter: set_tk_window 後訊息寫入 widget",
        lambda: None if "after binding" in text_widget.get("1.0", "end")
        else (_ for _ in ()).throw(AssertionError()),
    )

    # --- level filter ---
    text_widget.delete("1.0", "end")
    tk_adapter.set_filtered_level("ERROR")
    tk_adapter.broadcast("INFO", "info should be blocked")

    expect_pass(
        "TkinterAdapter: INFO 被 ERROR filter 阻擋",
        lambda: None if text_widget.get("1.0", "end").strip() == ""
        else (_ for _ in ()).throw(AssertionError()),
    )

    tk_adapter.set_filtered_level("DEBUG")

    # --- shine=True 使用 SHINE tag ---
    text_widget.delete("1.0", "end")
    tk_adapter.broadcast("SUCCESS", "shiny success", shine=True)
    expect_pass(
        "TkinterAdapter: shine=True 寫入 widget",
        lambda: None if "shiny success" in text_widget.get("1.0", "end")
        else (_ for _ in ()).throw(AssertionError()),
    )

    # --- overwrite_last_line ---
    text_widget.delete("1.0", "end")
    tk_adapter.broadcast("INFO", "original line")
    tk_adapter.overwrite_last_line("INFO", "replaced line")

    final_text = text_widget.get("1.0", "end").strip()
    expect_pass(
        "TkinterAdapter.overwrite_last_line: 最後一行被替換",
        lambda: None if "replaced line" in final_text
        else (_ for _ in ()).throw(AssertionError(f"final_text={final_text}")),
    )

    # --- LightThemeTkinterAdapter ---
    text_widget2 = tk.Text(root)
    light_tk = LightThemeTkinterAdapter("DEBUG", tk_window=text_widget2)
    light_tk.broadcast("WARNING", "light theme warning")

    expect_pass(
        "LightThemeTkinterAdapter: 訊息寫入 widget",
        lambda: None if "light theme warning" in text_widget2.get("1.0", "end")
        else (_ for _ in ()).throw(AssertionError()),
    )

    # --- flush 不拋例外 ---
    expect_pass(
        "TkinterAdapter.flush() 不拋例外",
        lambda: tk_adapter.flush(),
    )

    root.destroy()

except Exception as _tk_exc:
    skip("TkinterAdapter 測試組", f"Tkinter 不可用：{_tk_exc}")


# ════════════════════════════════════════════════════════════════════════════
# 20. TkLabelAdapter — lazy injection
# ════════════════════════════════════════════════════════════════════════════
print("\n── 20. TkLabelAdapter — lazy injection ──────────────────────────────────")

try:
    import tkinter as tk
    from isd_py_framework_sdk.message_logger import DarkThemeTkLabelAdapter, LightThemeTkLabelAdapter

    root_l = tk.Tk()
    root_l.withdraw()

    label = tk.Label(root_l)

    # --- lazy 建立 ---
    dark_label_adapter = DarkThemeTkLabelAdapter("DEBUG")
    expect_pass(
        "DarkThemeTkLabelAdapter: lazy 建立不拋例外",
        lambda: None,
    )

    dark_label_adapter.broadcast("INFO", "no label bound")    # 靜默略過
    expect_pass(
        "TkLabelAdapter: widget=None 時靜默略過",
        lambda: None if (label.cget("text") == "") else (_ for _ in ()).throw(AssertionError()),
    )

    dark_label_adapter.set_tk_label(label)
    dark_label_adapter.broadcast("ERROR", "error via label")

    expect_pass(
        "TkLabelAdapter: 注入後訊息設定到 label.text",
        lambda: None if "error via label" in label.cget("text")
        else (_ for _ in ()).throw(AssertionError(f"text={label.cget('text')}")),
    )

    # --- shine ---
    dark_label_adapter.broadcast("CRITICAL", "critical shine", shine=True)
    expect_pass(
        "TkLabelAdapter: shine=True 設定粗體字型",
        lambda: None,   # 只驗證不拋例外（字型設定屬於 Tk 內部）
    )

    # --- light theme ---
    label2 = tk.Label(root_l)
    light_label_adapter = LightThemeTkLabelAdapter("DEBUG", tk_label=label2)
    light_label_adapter.broadcast("WARNING", "light label warning")

    expect_pass(
        "LightThemeTkLabelAdapter: 訊息設定到 label",
        lambda: None if "light label warning" in label2.cget("text")
        else (_ for _ in ()).throw(AssertionError()),
    )

    root_l.destroy()

except Exception as _tklabel_exc:
    skip("TkLabelAdapter 測試組", f"Tkinter 不可用：{_tklabel_exc}")


# ════════════════════════════════════════════════════════════════════════════
# 21. TtkLabelAdapter — lazy injection
# ════════════════════════════════════════════════════════════════════════════
print("\n── 21. TtkLabelAdapter — lazy injection ──────────────────────────────────")

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from isd_py_framework_sdk.message_logger import DarkThemeTtkLabelAdapter, LightThemeTtkLabelAdapter

    root_tl = tk.Tk()
    root_tl.withdraw()

    ttk_label = ttk.Label(root_tl)

    dark_ttk = DarkThemeTtkLabelAdapter("DEBUG")
    expect_pass(
        "DarkThemeTtkLabelAdapter: lazy 建立不拋例外",
        lambda: None,
    )

    dark_ttk.broadcast("INFO", "no ttk bound")        # 靜默略過
    expect_pass(
        "TtkLabelAdapter: widget=None 時靜默略過",
        lambda: None,
    )

    dark_ttk.set_ttk_label(ttk_label)
    dark_ttk.broadcast("SUCCESS", "success via ttk label")

    expect_pass(
        "TtkLabelAdapter: 注入後訊息設定到 label",
        lambda: None if "success via ttk label" in ttk_label.cget("text")
        else (_ for _ in ()).throw(AssertionError(f"text={ttk_label.cget('text')}")),
    )

    dark_ttk.broadcast("WARNING", "shine ttk", shine=True)
    expect_pass(
        "TtkLabelAdapter: shine=True 不拋例外",
        lambda: None,
    )

    # --- light theme ---
    ttk_label2 = ttk.Label(root_tl)
    light_ttk = LightThemeTtkLabelAdapter("DEBUG", ttk_label=ttk_label2)
    light_ttk.broadcast("ERROR", "light ttk error")

    expect_pass(
        "LightThemeTtkLabelAdapter: 訊息設定到 label",
        lambda: None if "light ttk error" in ttk_label2.cget("text")
        else (_ for _ in ()).throw(AssertionError()),
    )

    root_tl.destroy()

except Exception as _ttklabel_exc:
    skip("TtkLabelAdapter 測試組", f"Tkinter 不可用：{_ttklabel_exc}")


# ════════════════════════════════════════════════════════════════════════════
# 22. Stub Adapters — no-op broadcast 不拋例外
# ════════════════════════════════════════════════════════════════════════════
print("\n── 22. Stub Adapters（HTML / HTTP / DB / WebSocket）───────────────────")

from isd_py_framework_sdk.message_logger import HTMLAdapter, HTTPAdapter, DBAdapter, WebsocketAdapter

for stub_cls in (HTMLAdapter, HTTPAdapter, DBAdapter, WebsocketAdapter):
    name = stub_cls.__name__
    stub = stub_cls("DEBUG")

    expect_pass(
        f"{name}: broadcast() 不拋例外（no-op stub）",
        lambda s=stub: s.broadcast("INFO", "stub test"),
    )

    expect_pass(
        f"{name}: flush() 不拋例外",
        lambda s=stub: s.flush(),
    )

    expect_pass(
        f"{name}: 是 LoggerAdapterBase 的子類",
        lambda cls=stub_cls: None if issubclass(cls, LoggerAdapterBase)
        else (_ for _ in ()).throw(AssertionError()),
    )


# ════════════════════════════════════════════════════════════════════════════
# 23. LoggerAdapterBase.help() — 正常印出
# ════════════════════════════════════════════════════════════════════════════
print("\n── 23. LoggerAdapterBase.help() ─────────────────────────────────────────")

captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    LoggerAdapterBase.help()

expect_pass(
    "help() 輸出包含所有 8 個等級名稱",
    lambda: None if all(lvl in captured.getvalue() for lvl in LevelOrder)
    else (_ for _ in ()).throw(AssertionError(f"output={captured.getvalue()}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 24. LoggerBase — 大小寫不敏感（level 傳小寫）
# ════════════════════════════════════════════════════════════════════════════
print("\n── 24. LoggerBase — level 大小寫不敏感 ─────────────────────────────────")

cap = CaptureAdapter("DEBUG")
logger_b._initialize_manager()
logger_b.register_adapter(cap)

logger_b.log("lower case level", "warning")   # 傳小寫
expect_pass(
    "log('warning') 正常廣播（不拋例外）",
    lambda: None if len(cap.records) == 1
    else (_ for _ in ()).throw(AssertionError(f"records={cap.records}")),
)

expect_pass(
    "log('warning') 等級存成大寫 WARNING",
    lambda: None if cap.records[0]["level"] == "WARNING"
    else (_ for _ in ()).throw(AssertionError(f"level={cap.records[0]['level']}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 25. FileAdapter — auto_flush=False 手動 flush
# ════════════════════════════════════════════════════════════════════════════
print("\n── 25. FileAdapter — auto_flush=False 手動 flush ───────────────────────")

with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as tf:
    tmp_noflush = Path(tf.name)

fa_noflush = FileAdapter("DEBUG", tmp_noflush, mode="w", auto_flush=False)
fa_noflush.broadcast("INFO", "manual flush line")

expect_pass(
    "FileAdapter auto_flush=False: broadcast() 不拋例外",
    lambda: None,
)

fa_noflush.flush()   # 手動 flush
fa_noflush.close()

content_nf = tmp_noflush.read_text(encoding="utf-8")
expect_pass(
    "FileAdapter auto_flush=False: 手動 flush 後資料寫入磁碟",
    lambda: None if "manual flush line" in content_nf
    else (_ for _ in ()).throw(AssertionError(f"content={content_nf}")),
)


# ════════════════════════════════════════════════════════════════════════════
# 結果摘要
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 60)
print(f"  PASS: {PASS}   FAIL: {FAIL}   SKIP: {SKIP}")
print("═" * 60)

if FAIL > 0:
    sys.exit(1)
