"""
QueuedSocketAdapter skeleton demo.

This demonstrates injection only. It is intentionally simple:
- queue + worker avoids blocking logger.broadcast call path
- UDP/TCP send is best-effort for now

Future extension ideas:
1) persistent TCP connection + reconnect/backoff
2) ack/retry and batching
3) asyncio-based transport
"""

from isd_py_framework_sdk.message_logger import QueuedSocketAdapter, SingletonSystemLogger


def main() -> None:
    logger = SingletonSystemLogger()
    logger.clear_adapters()

    socket_adapter = QueuedSocketAdapter(
        "INFO",
        host="127.0.0.1",
        port=9020,
        protocol="udp",
        max_queue_size=128,
        fail_silently=True,
    )
    logger.register_adapter(socket_adapter)

    logger.info("socket-demo: service started")
    logger.warning("socket-demo: queueing event")
    logger.error("socket-demo: simulated error")

    logger.flush_all()
    socket_adapter.close()


if __name__ == "__main__":
    main()
