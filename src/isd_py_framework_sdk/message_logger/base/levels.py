"""
Log level definitions.
Contains `LogLevelLiteral` and `LevelOrder` used by adapters and LoggerBase.
"""
from typing import Literal

LogLevelLiteral = Literal[
    "DEBUG",
    "INFO", "CHECKPOINT",
    "SUCCESS", "WARNING", "ERROR", "CRITICAL",
    "HIGHLIGHT",
]

LevelOrder: dict[str, int] = {
    "DEBUG":      10,  # 詳細除錯，開發階段有用，平時不顯示
    "INFO":       20,  # 正常運行狀態、流程資訊
    "CHECKPOINT": 22,  # 流程檢查點，讓關鍵節點訊息更明顯
    "SUCCESS":    25,  # 特殊的成功狀態訊息，比 INFO 更突出
    "WARNING":    30,  # 潛在問題、非致命警告
    "ERROR":      40,  # 錯誤，操作失敗需修正
    "CRITICAL":   50,  # 致命錯誤，系統無法正常運作
    "HIGHLIGHT":  60,  # 超醒目標記
}
