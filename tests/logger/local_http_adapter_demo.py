"""
LocalHTTPAdapter MVP demo.

Run listener first (example):
    uvicorn tests.logger.local_http_listener:app --reload --port 8000

Then run this script:
    python tests/logger/local_http_adapter_demo.py
"""

from pathlib import Path

from isd_py_framework_sdk.message_logger import (
    DarkThemeTerminalAdapter,
    FileAdapter,
    LocalHTTPAdapter,
    SingletonSystemLogger,
)


def main() -> None:
    logger = SingletonSystemLogger()
    logger.clear_adapters()

    logger.register_adapter(DarkThemeTerminalAdapter("DEBUG"))
    logger.register_adapter(FileAdapter("INFO", Path("local_http_demo.log"), mode="w"))

    # MVP: send JSON logs to local HTTP endpoint.
    logger.register_adapter(
        LocalHTTPAdapter(
            "INFO",
            endpoint_url="http://127.0.0.1:8000/logs",
            timeout=0.5,
            fail_silently=True,
        )
    )

    logger.debug("debug message (HTTP adapter filter will skip this)")
    logger.info("service boot")
    logger.warning("high memory usage")
    logger.error("network retry exhausted")
    logger.shiny_log("milestone reached", "SUCCESS")

    logger.flush_all()


if __name__ == "__main__":
    main()
