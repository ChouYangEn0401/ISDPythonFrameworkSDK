"""
Simple local socket listener for QueuedSocketAdapter demos.

Usage (UDP):
    python tests/logger/socket_listener.py --protocol udp --host 127.0.0.1 --port 9020

Usage (TCP):
    python tests/logger/socket_listener.py --protocol tcp --host 127.0.0.1 --port 9020
"""

from __future__ import annotations

import argparse
import json
import socket
from pathlib import Path
from typing import Any
from isd_py_framework_sdk.message_logger import FileAdapter


def _format_payload(raw: bytes, addr: tuple[str, int] | None = None) -> str:
    line = raw.decode("utf-8", errors="replace").strip()
    if not line:
        return ""

    try:
        payload: dict[str, Any] = json.loads(line)
        prefix = f"[{addr[0]}:{addr[1]}] " if addr else ""
        return (
            f"{prefix}recv level={payload.get('level')} "
            f"shine={payload.get('shine')} formatted={payload.get('formatted')}"
        )
    except json.JSONDecodeError:
        prefix = f"[{addr[0]}:{addr[1]}] " if addr else ""
        return f"{prefix}recv raw={line}"


def run_udp(host: str, port: int, output_file: Path, max_messages: int) -> None:
    received_count = 0
    file_adapter = FileAdapter("DEBUG", output_file, mode="w")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        print(f"UDP listener started at {host}:{port} (max_messages={max_messages}, output_file={output_file})")
        while received_count < max_messages:
            data, addr = sock.recvfrom(65535)
            line = _format_payload(data, addr)
            if not line:
                continue
            received_count += 1
            file_adapter.broadcast("INFO", line)
            print(f"[{received_count}/{max_messages}] {line}")

        print("UDP listener reached max messages and will exit.")
    file_adapter.close()


def _drain_tcp_buffer(buf: str) -> tuple[list[str], str]:
    if "\n" not in buf:
        return [], buf
    parts = buf.split("\n")
    return parts[:-1], parts[-1]


def run_tcp(host: str, port: int, output_file: Path, max_messages: int) -> None:
    received_count = 0
    file_adapter = FileAdapter("DEBUG", output_file, mode="w")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"TCP listener started at {host}:{port} (max_messages={max_messages}, output_file={output_file})")

        while received_count < max_messages:
            conn, addr = server.accept()
            with conn:
                buf = ""
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    buf += chunk.decode("utf-8", errors="replace")
                    lines, buf = _drain_tcp_buffer(buf)
                    for line in lines:
                        formatted = _format_payload(line.encode("utf-8", errors="replace"), addr)
                        if not formatted:
                            continue
                        received_count += 1
                        file_adapter.broadcast("INFO", formatted)
                        print(f"[{received_count}/{max_messages}] {formatted}")
                        if received_count >= max_messages:
                            print("TCP listener reached max messages and will exit.")
                            file_adapter.close()
                            return
                if buf.strip():
                    formatted = _format_payload(buf.encode("utf-8", errors="replace"), addr)
                    if not formatted:
                        continue
                    received_count += 1
                    file_adapter.broadcast("INFO", formatted)
                    print(f"[{received_count}/{max_messages}] {formatted}")
                    if received_count >= max_messages:
                        print("TCP listener reached max messages and will exit.")
                        file_adapter.close()
                        return
    file_adapter.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Socket listener for QueuedSocketAdapter demo")
    parser.add_argument("--protocol", choices=["udp", "tcp"], default="udp")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9020)
    parser.add_argument("--max-messages", type=int, default=3)
    parser.add_argument(
        "--output-file",
        default=str(Path(__file__).with_name("socket_listener.log")),
        help="path to append received logs",
    )
    args = parser.parse_args()
    output_file = Path(args.output_file)

    if args.protocol == "tcp":
        run_tcp(args.host, args.port, output_file, args.max_messages)
    else:
        run_udp(args.host, args.port, output_file, args.max_messages)


if __name__ == "__main__":
    main()
