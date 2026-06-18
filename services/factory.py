"""Site adapter factory."""

from __future__ import annotations

from services.base import BaseSiteAdapter
from services.site_netease import NeteaseSiteAdapter
from services.site_tencent import TencentSiteAdapter


def get_site_adapter(source: str) -> BaseSiteAdapter:
    adapters = {
        "qq": TencentSiteAdapter,
        "tencent": TencentSiteAdapter,
        "netease": NeteaseSiteAdapter,
    }
    cls = adapters.get(source.lower())
    if not cls:
        raise ValueError(f"Unsupported site: {source}")
    return cls()
