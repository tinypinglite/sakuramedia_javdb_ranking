"""按任务运行隔离 JavDB 匿名 client，避免跨线程共享连接。"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class PerRunClientHolder:
    """同一任务运行复用 client，不同线程/运行使用新实例。"""

    def __init__(self, factory: Callable[[], Any]):
        self._factory = factory
        self._local = threading.local()

    def fresh_for_current_thread(self) -> Any:
        self.close_current_thread()
        client = self._factory()
        self._local.client = client
        return client

    def get(self) -> Any:
        client = getattr(self._local, "client", None)
        if client is None:
            client = self.fresh_for_current_thread()
        return client

    def close_current_thread(self) -> None:
        client = getattr(self._local, "client", None)
        self._local.client = None
        if client is not None:
            close = getattr(client, "close", None)
            if close is not None:
                close()
