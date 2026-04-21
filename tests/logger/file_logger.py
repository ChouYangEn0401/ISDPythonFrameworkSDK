from pathlib import Path
from isd_py_framework_sdk.message_logger import SingletonSystemLogger, FileAdapter, DarkThemeTerminalAdapter

logger = SingletonSystemLogger()
logger.clear_adapters()
logger.register_adapter(FileAdapter("WARNING", Path("app.log")))

logger.info("這行不會進檔案")          # 被 WARNING 過濾掉
logger.warning("這行會進檔案")
logger.error("這行也會進檔案")

# 驗證寫入內容
print(Path("app.log").read_text(encoding="utf-8"))