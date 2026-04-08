from hyper_framework.base.Singleton import SingletonMetaclass as SingletonMetaclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tkinter import Text

class SingletonSystemLogger(metaclass=SingletonMetaclass):
    LogLevelLiteral = Literal[
        "DEBUG", "INFO",
        "CHECKPOINT", "SUCCESS", "WARNING",
        "ERROR", "CRITICAL",
        "HIGHLIGHT"
    ]

    """
        專業的單例 SingletonSystemLogger，支援等級過濾、對齊、顏色與多種輸出模式。

        Log Levels（由低到高）：
            DEBUG:        用於詳細調試資訊，開發時用，平時一般不顯示。
            INFO:         重要的正常運行訊息，例如系統啟動、完成某任務。
            CHECKPOINT:   流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯。
            SUCCESS:      特殊的成功訊息，表示某個操作成功完成，比 INFO 更突出成功狀態。
            WARNING:      警告訊息，提示可能有問題但不影響運行。
            ERROR:        錯誤訊息，表示操作失敗或重要錯誤，需要關注。
            CRITICAL:     致命錯誤，系統崩潰或無法繼續執行，需要立即處理。
            HIGHLIGHT:   超醒目提示。
    """
    @staticmethod
    def help() -> None:
        """ Show The Level For Each Usable Mode """
        ...
    def set_min_level(self, level: LogLevelLiteral):
        """ Set The Lowest Showcase Level """
        ...
    def set_output_mode(self, mode: Literal['console', 'file', 'both']):
        """ Set Message OutPut Mode """
        ...
    def set_log_file(self, filepath: str):
        """ Set Output Place To Local File """
        ...
    def enable(self) -> None:
        """ Allow Logger To Take Action """
        ...
    def disable(self) -> None:
        """ Disallow Logger To Take Action """
        ...
    def set_window(self, text_widget: Text):
        """ Set Output Place To Existed Text Widget In Tkinter Window """
        ...
    def shiny_log(self, message: str, level: LogLevelLiteral = 'INFO'):
        """ ShinyMode=True, Log """
        ...

    def log(self, message: str, level: LogLevelLiteral = "INFO", shine: bool = False):
        """
            Log Text
            Log Levels（由低到高）：
                DEBUG:        用於詳細調試資訊，開發時用，平時一般不顯示。
                INFO:         重要的正常運行訊息，例如系統啟動、完成某任務。
                CHECKPOINT:   流程檢查點，介於 INFO 與 SUCCESS 之間，讓關鍵節點訊息更明顯。
                SUCCESS:      特殊的成功訊息，表示某個操作成功完成，比 INFO 更突出成功狀態。
                WARNING:      警告訊息，提示可能有問題但不影響運行。
                ERROR:        錯誤訊息，表示操作失敗或重要錯誤，需要關注。
                CRITICAL:     致命錯誤，系統崩潰或無法繼續執行，需要立即處理。
                HIGHLIGHT:   超醒目提示。
            ShinyMode=False
        """
        ...
    def debug(self, msg: str): ...
    def info(self, msg: str): ...
    def checkpoint(self, msg: str): ...
    def success(self, msg: str): ...
    def warning(self, msg: str): ...
    def error(self, msg: str): ...
    def critical(self, msg: str): ...
    def highlight(self, msg: str): ...

def test_logger_basic_flow() -> None: ...
def test_logger_level_order_and_aliases() -> None: ...
def test_logger_file_output_content() -> None: ...
def tkinter_gui_text_testing() -> None: ...
