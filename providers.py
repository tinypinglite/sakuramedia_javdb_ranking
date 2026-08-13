"""按任务运行隔离 JavDB provider，避免登录失败状态跨运行/跨线程污染。"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class PerRunProviderHolder:
    """每个任务运行开始时换新 provider；同一运行的各 board 复用线程本地实例。

    宿主 worker 默认 4 并发，全量同步与手动单榜同步是不同 task_key、可并发执行；
    用线程本地保证各运行互不干扰。JavdbProvider 登录失败后同实例不再重试，
    因此每次运行必须换新实例，失败只影响当次运行。
    """

    def __init__(self, factory: Callable[[], Any]):
        self._factory = factory
        self._local = threading.local()

    def fresh_for_current_thread(self) -> Any:
        provider = self._factory()
        self._local.provider = provider
        return provider

    def get(self) -> Any:
        provider = getattr(self._local, "provider", None)
        if provider is None:
            provider = self.fresh_for_current_thread()
        return provider
