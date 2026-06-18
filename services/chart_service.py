"""Latest charts catalog and live fetch service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from services.common_parser import ChartRecord, TrackRecord
from services.factory import get_site_adapter
from skills.executor import SkillExecutor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "config" / "charts_catalog.json"


def load_charts_catalog() -> dict[str, Any]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_charts(source: Optional[str] = None) -> list[dict[str, Any]]:
    catalog = load_charts_catalog()
    result = []
    for site_id, site_data in catalog.items():
        if source and site_id != source:
            continue
        for chart in site_data.get("charts", []):
            result.append({
                "source": site_id,
                "site_name": site_data.get("site_name", site_id),
                **chart,
            })
    return result


async def fetch_latest_chart(
    source: str,
    chart_type: str = "hot",
    limit: int = 50,
) -> ChartRecord:
    """Fetch live latest chart from music site."""
    catalog = load_charts_catalog()
    site_data = catalog.get(source)
    if not site_data:
        raise ValueError(f"Unknown source: {source}")

    chart_def = next((c for c in site_data["charts"] if c["id"] == chart_type), None)
    if not chart_def:
        raise ValueError(f"Unknown chart type: {chart_type} for {source}")

    adapter = get_site_adapter(source)

    if source == "qq":
        return await _fetch_qq_chart(adapter, chart_def, limit)
    if source == "netease":
        return await _fetch_netease_chart(adapter, chart_def, limit)

    raise ValueError(f"Unsupported source: {source}")


async def _fetch_qq_chart(adapter, chart_def: dict, limit: int) -> ChartRecord:
    topid = chart_def["topid"]
    data = await adapter._request(
        "hot_chart",
        extra_params={"topid": topid},
    )
    adapter._cache_response(f"chart_{chart_def['id']}", data)

    song_list = []
    if "songlist" in data:
        song_list = [item.get("data", item) for item in data["songlist"][:limit]]

    skill = SkillExecutor()
    cleaned = skill._data_clean({"raw_data": song_list, "source": "qq"})
    tracks = [TrackRecord(**t) for t in cleaned.get("tracks", [])[:limit]]

    update_time = data.get("date") or data.get("update_time") or datetime.now(timezone.utc).isoformat()

    return ChartRecord(
        chart_id=f"qq_{chart_def['id']}_{topid}",
        source="qq",
        name=f"QQ音乐{chart_def['name']}",
        tracks=tracks,
    )


async def _fetch_netease_chart(adapter, chart_def: dict, limit: int) -> ChartRecord:
    playlist_id = chart_def["playlist_id"]
    data = await adapter._request(
        "hot_chart",
        extra_params={"id": playlist_id},
    )
    adapter._cache_response(f"chart_{chart_def['id']}", data)

    playlist = data.get("playlist", data.get("result", {}))
    if isinstance(playlist, dict) and "playlist" in playlist:
        playlist = playlist["playlist"]

    tracks_raw = playlist.get("tracks", [])[:limit]
    update_time = playlist.get("updateTime") or playlist.get("trackUpdateTime")

    skill = SkillExecutor()
    cleaned = skill._data_clean({"raw_data": tracks_raw, "source": "netease"})
    tracks = [TrackRecord(**t) for t in cleaned.get("tracks", [])[:limit]]

    chart = ChartRecord(
        chart_id=f"netease_{chart_def['id']}_{playlist_id}",
        source="netease",
        name=f"网易云{chart_def['name']}",
        tracks=tracks,
    )
    return chart


async def fetch_all_latest(source: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch all chart types for a source."""
    catalog = load_charts_catalog()
    charts_meta = catalog.get(source, {}).get("charts", [])
    results = []

    for chart_def in charts_meta:
        try:
            chart = await fetch_latest_chart(source, chart_def["id"], limit)
            results.append({
                "chart_type": chart_def["id"],
                "chart_name": chart_def["name"],
                "description": chart_def.get("description", ""),
                "source": source,
                "track_count": len(chart.tracks),
                "tracks": [t.model_dump(mode="json") for t in chart.tracks],
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            results.append({
                "chart_type": chart_def["id"],
                "chart_name": chart_def["name"],
                "source": source,
                "error": str(e),
                "tracks": [],
            })

    return results
