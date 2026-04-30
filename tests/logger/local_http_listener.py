"""
Minimal FastAPI listener for LocalHTTPAdapter MVP.

Install:
    pip install fastapi uvicorn

Run (standalone):
    python tests/logger/local_http_listener.py --host 127.0.0.1 --port 8000

Run (uvicorn module mode):
    uvicorn tests.logger.local_http_listener:app --reload --port 8000
"""

from __future__ import annotations

import argparse
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from isd_py_framework_sdk.message_logger import FileAdapter, LevelOrder


class LogPayload(BaseModel):
    level: str
    shine: bool = False
    formatted: str | None = None


app = FastAPI(title="Local Logger Listener")
_LOCK = Lock()

# Default runtime state for module mode (uvicorn import).
app.state.received_count = 0
app.state.max_messages = 3
app.state.output_file = Path(__file__).with_name("http_listener.log")
app.state.server = None
app.state.file_adapter = FileAdapter("DEBUG", app.state.output_file, mode="a")


def _safe_level(level: str) -> str:
    normalized = level.upper()
    return normalized if normalized in LevelOrder else "INFO"


@app.post("/logs")
def receive_log(payload: LogPayload) -> dict:
    line = f"level={payload.level} shine={payload.shine} msg={payload.formatted}"
    with _LOCK:
        if app.state.received_count >= app.state.max_messages:
            ignored_at = app.state.received_count
            print(f"[listener ignored] {line}")
            return {
                "ok": False,
                "ignored": True,
                "received_count": ignored_at,
                "max_messages": app.state.max_messages,
            }

        app.state.received_count += 1
        count = app.state.received_count
        app.state.file_adapter.broadcast(_safe_level(payload.level), line)

    print(f"[listener #{count}] {line}")

    # Auto-stop after N messages for quick verification workflow.
    if count >= app.state.max_messages and app.state.server is not None:
        app.state.server.should_exit = True

    return {
        "ok": True,
        "received_count": count,
        "max_messages": app.state.max_messages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Local HTTP listener for LocalHTTPAdapter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-messages", type=int, default=3)
    parser.add_argument(
        "--output-file",
        default=str(Path(__file__).with_name("http_listener.log")),
        help="path to append received logs",
    )
    args = parser.parse_args()

    app.state.received_count = 0
    app.state.max_messages = args.max_messages
    app.state.output_file = Path(args.output_file)
    app.state.file_adapter = FileAdapter("DEBUG", app.state.output_file, mode="w")

    print(
        f"HTTP listener started at http://{args.host}:{args.port}/logs "
        f"(max_messages={args.max_messages}, output_file={app.state.output_file})"
    )

    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
    server = uvicorn.Server(config)
    app.state.server = server
    server.run()


if __name__ == "__main__":
    main()
