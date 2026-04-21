from isd_py_framework_sdk.base.Singleton import SingletonMetaclass
from isd_py_framework_sdk.message_logger.logger import LoggerBase


class SingletonSystemLogger(LoggerBase, metaclass=SingletonMetaclass):
    """
        全域單例 Logger。

        繼承 LoggerBase 取得格式化與 fan-out 能力，
        並透過 SingletonMetaclass 保證整個執行期只有一個實例。

        使用方式：
            logger = SingletonSystemLogger()
            logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))
            logger.register_adapter(FileAdapter("WARNING", Path("app.log")))

            logger.info("系統啟動")
            logger.error("發生錯誤")
            logger.shiny_log("關鍵里程碑", "CHECKPOINT")

        注意：
            SingletonMetaclass 會在第一次建立實例後自動呼叫 _initialize_manager()，
            不需要也不應該手動呼叫。後續透過 register_adapter 新增輸出目標。
    """
    pass
