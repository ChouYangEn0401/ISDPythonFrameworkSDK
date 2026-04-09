"""
Log level definitions (moved from `enum.py` to avoid shadowing stdlib `enum`).
Contains `LogLevelLiteral` and `LevelOrder` used by adapters/logger.
"""
from typing import Optional, Literal, TYPE_CHECKING

LogLevelLiteral = Literal[
    "DEBUG", 
    "INFO", "CHECKPOINT", 
    "SUCCESS", "WARNING", "ERROR", "CRITICAL",
    "HIGHLIGHT"
]

LevelOrder = {
    "DEBUG": 10,  # 詳細除錯，開發階段有用，平時不顯示
    
    "INFO": 20,  # 正常運行狀態、流程資訊
    "CHECKPOINT": 22,  # 流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯
    
    "SUCCESS": 25,  # 特殊的成功狀態訊息，比 INFO 更突出
    "WARNING": 30,  # 潛在問題、非致命警告
    "ERROR": 40,  # 錯誤，操作失敗需修正
    "CRITICAL": 50,  # 致命錯誤，系統無法正常運作

    "HIGHLIGHT": 60,  # 炫泡的燈光效果？？
}
