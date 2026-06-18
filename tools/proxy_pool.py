"""Proxy pool tool for IP rotation."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ProxyPool:
    """Simple proxy pool with optional external proxy list."""

    def __init__(self, proxies: Optional[list[str]] = None):
        self._proxies = proxies or []
        self._index = 0
        self._enabled = False

    def load_from_file(self, path: Path) -> None:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self._proxies = data.get("proxies", [])

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled and len(self._proxies) > 0

    def get_next(self) -> Optional[str]:
        if not self.enabled:
            return None
        proxy = self._proxies[self._index % len(self._proxies)]
        self._index += 1
        return proxy

    def get_random(self) -> Optional[str]:
        if not self.enabled:
            return None
        return random.choice(self._proxies)

    def add_proxy(self, proxy: str) -> None:
        if proxy not in self._proxies:
            self._proxies.append(proxy)

    def list_proxies(self) -> list[str]:
        return list(self._proxies)


_default_pool = ProxyPool()


def get_proxy_pool() -> ProxyPool:
    return _default_pool
