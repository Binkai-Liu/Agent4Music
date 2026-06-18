"""NetEase Cloud Music public data adapter."""

from __future__ import annotations

from services.base import BaseSiteAdapter
from services.common_parser import ArtistRecord, ChartRecord, TrackRecord
from skills.executor import SkillExecutor


class NeteaseSiteAdapter(BaseSiteAdapter):
    site_id = "netease"

    async def fetch_hot_chart(self, limit: int = 50) -> ChartRecord:
        data = await self._request("hot_chart")
        self._cache_response("hot_chart", data)

        playlist = data.get("playlist", data.get("result", {}))
        if isinstance(playlist, dict) and "playlist" in playlist:
            playlist = playlist["playlist"]

        tracks_raw = playlist.get("tracks", [])[:limit]

        skill = SkillExecutor()
        cleaned = skill._data_clean({"raw_data": tracks_raw, "source": "netease"})

        tracks = [TrackRecord(**t) for t in cleaned.get("tracks", [])[:limit]]

        return ChartRecord(
            chart_id="netease_hot",
            source="netease",
            name="网易云热歌榜",
            tracks=tracks,
        )

    async def fetch_playlist(self, playlist_id: str) -> list[TrackRecord]:
        data = await self._request(
            "playlist_detail",
            extra_params={"id": playlist_id},
        )
        self._cache_response(f"playlist_{playlist_id}", data)

        playlist = data.get("playlist", data.get("result", {}))
        if isinstance(playlist, dict) and "playlist" in playlist:
            playlist = playlist["playlist"]

        tracks_raw = playlist.get("tracks", [])

        skill = SkillExecutor()
        cleaned = skill._data_clean({"raw_data": tracks_raw, "source": "netease"})
        return [TrackRecord(**t) for t in cleaned.get("tracks", [])]

    async def fetch_artist(self, artist_id: str) -> ArtistRecord:
        data = await self._request(
            "artist_info",
            extra_params={"id": artist_id},
        )
        self._cache_response(f"artist_{artist_id}", data)

        desc_data = data.get("briefDesc", data.get("description", ""))
        if isinstance(desc_data, dict):
            desc = desc_data.get("briefDesc", "")
        else:
            desc = str(desc_data) if desc_data else ""

        return ArtistRecord(
            artist_id=artist_id,
            source="netease",
            name=data.get("name", "Unknown"),
            description=desc[:500] if desc else None,
            avatar_url=data.get("picUrl"),
        )
