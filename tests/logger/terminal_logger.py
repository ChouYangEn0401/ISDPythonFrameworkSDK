from hyper_framework.msg_logger import SingletonSystemLogger, DarkThemeTerminalAdapter

logger = SingletonSystemLogger()
logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))

logger.debug("除錯訊息")
logger.info("正常流程")
logger.checkpoint("關鍵節點")
logger.success("操作成功")
logger.warning("注意事項")
logger.error("發生錯誤")
logger.critical("致命錯誤")
logger.highlight("超醒目")
logger.shiny_log("閃亮登場", "SUCCESS")