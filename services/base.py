"""Base site adapter for music platforms."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import httpx

from services.common_parser import ArtistRecord, ChartRecord, TrackRecord, track_to_dict
from utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class BaseSiteAdapter(ABC):
    site_id: str = ""
    site_name: str = ""

    def __init__(self, rules_path: Optional[Path] = None):
        path = rules_path or PROJECT_ROOT / "config" / "spider_rules" / f"{self.site_id}.json"
        with open(path, encoding="utf-8") as f:
            self.rules = json.load(f)
        self.site_name = self.rules.get("site_name", self.site_id)
        self.rate_limit_ms = self.rules.get("rate_limit_ms", 1500)

    @abstractmethod
    async def fetch_hot_chart(self, limit: int = 50) -> ChartRecord:
        pass

    @abstractmethod
    async def fetch_playlist(self, playlist_id: str) -> list[TrackRecord]:
        pass

    @abstractmethod
    async def fetch_artist(self, artist_id: str) -> ArtistRecord:
        pass

    async def _request(
        self,
        endpoint_key: str,
        extra_params: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
    ) -> dict[str, Any]:
        endpoint = self.rules["endpoints"].get(endpoint_key, {})
        url = endpoint.get("url", "")
        params = {**endpoint.get("params", {}), **(extra_params or {})}
        method = endpoint.get("method", "GET").upper()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.rules.get("base_url", ""),
            **(extra_headers or {}),
        }

        import asyncio
        await asyncio.sleep(self.rate_limit_ms / 1000.0)

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.request(method, url, params=params, headers=headers)
            text = response.text

            if "callback(" in text:
                text = text[text.index("(") + 1 : text.rindex(")")]

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw_text": text, "status_code": response.status_code}

    def _cache_response(self, key: str, data: Any) -> None:
        cache_dir = PROJECT_ROOT / "data" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.site_id}_{key}.json"
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
