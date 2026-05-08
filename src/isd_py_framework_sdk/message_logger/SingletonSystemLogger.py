from isd_py_framework_sdk.base.Singleton import SingletonMetaclass
from isd_py_framework_sdk.message_logger.base.LoggerBase import LoggerBase

from isd_py_framework_sdk.message_logger.base.levels import LogLevelLiteral
from isd_py_framework_sdk.message_logger.adapters import LoggerAdapterBase


class SingletonSystemLogger(LoggerBase, metaclass=SingletonMetaclass):
    """
        全域單例 Logger。

        繼承 LoggerBase 取得格式化與 fan-out 能力，
        並透過 SingletonMetaclass 保證整個執行期只有一個實例。

        典型使用方式：
            logger = SingletonSystemLogger()
            logger.add_adapter(DarkThemeTerminalAdapter(level_filter="DEBUG"))
            logger.add_adapter(FileAdapter(level_filter="WARNING", output_file=Path("app.log")))

            logger.info("系統啟動")
            logger.error("發生錯誤")
            logger.shiny_log("關鍵里程碑", "CHECKPOINT")

        注意：
            SingletonMetaclass 會在第一次建立實例後自動呼叫 _initialize_manager()，
            不需要也不應該手動呼叫。後續透過 add_adapter 新增輸出目標即可。
    """
    pass
