"""QQ Music (Tencent) public data adapter."""

from __future__ import annotations

from typing import Any

from services.base import BaseSiteAdapter
from services.common_parser import ArtistRecord, ChartRecord, TrackRecord, get_nested, normalize_duration
from skills.executor import SkillExecutor


class TencentSiteAdapter(BaseSiteAdapter):
    site_id = "qq"

    async def fetch_hot_chart(self, limit: int = 50) -> ChartRecord:
        data = await self._request("hot_chart")
        self._cache_response("hot_chart", data)

        song_list = []
        if "songlist" in data:
            song_list = [item.get("data", item) for item in data["songlist"][:limit]]
        elif "detail" in data and "data" in data.get("detail", {}):
            song_list = data["detail"]["data"].get("songInfoList", [])[:limit]

        skill = SkillExecutor()
        cleaned = skill._data_clean({"raw_data": song_list, "source": "qq"})

        tracks = [TrackRecord(**t) for t in cleaned.get("tracks", [])[:limit]]

        return ChartRecord(
            chart_id="qq_hot_26",
            source="qq",
            name="QQ音乐热歌榜",
            tracks=tracks,
        )

    async def fetch_playlist(self, playlist_id: str) -> list[TrackRecord]:
        data = await self._request(
            "playlist_detail",
            extra_params={"disstid": playlist_id},
        )
        self._cache_response(f"playlist_{playlist_id}", data)

        cdlist = data.get("cdlist", [])
        songs = []
        if cdlist:
            songs = cdlist[0].get("songlist", [])

        skill = SkillExecutor()
        cleaned = skill._data_clean({"raw_data": songs, "source": "qq"})
        return [TrackRecord(**t) for t in cleaned.get("tracks", [])]

    async def fetch_artist(self, artist_id: str) -> ArtistRecord:
        data = await self._request(
            "artist_info",
            extra_params={"singermid": artist_id},
        )
        self._cache_response(f"artist_{artist_id}", data)

        info = data.get("data", {}).get("info", {})
        desc = data.get("data", {}).get("desc", "")

        return ArtistRecord(
            artist_id=artist_id,
            source="qq",
            name=info.get("name", info.get("singer_name", "Unknown")),
            description=desc[:500] if desc else None,
            avatar_url=info.get("pic"),
        )
