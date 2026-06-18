"""Unified track schema and common parsing utilities."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class TrackRecord(BaseModel):
    track_id: str
    source: str
    title: str
    artists: list[str] = Field(default_factory=list)
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    play_count: Optional[int] = None
    chart_rank: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    lyric_raw: Optional[str] = None
    cover_url: Optional[str] = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def dedup_key(self) -> str:
        raw = f"{self.source}:{self.track_id}:{self.title}"
        return hashlib.md5(raw.encode()).hexdigest()


class ArtistRecord(BaseModel):
    artist_id: str
    source: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    track_count: Optional[int] = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChartRecord(BaseModel):
    chart_id: str
    source: str
    name: str
    tracks: list[TrackRecord] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def get_nested(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """Get nested value using dot notation, e.g. 'singer.0.name'."""
    keys = path.split(".")
    current: Any = data
    for key in keys:
        if current is None:
            return default
        if key.isdigit():
            idx = int(key)
            if isinstance(current, list) and idx < len(current):
                current = current[idx]
            else:
                return default
        elif isinstance(current, dict):
            current = current.get(key)
        else:
            return default
    return current if current is not None else default


def normalize_duration(value: Any, source: str) -> Optional[int]:
    """Normalize duration to milliseconds."""
    if value is None:
        return None
    try:
        v = int(value)
        if source == "qq":
            return v * 1000
        return v
    except (TypeError, ValueError):
        return None


def deduplicate_tracks(tracks: list[TrackRecord]) -> list[TrackRecord]:
    seen: set[str] = set()
    result: list[TrackRecord] = []
    for track in tracks:
        key = track.dedup_key()
        if key not in seen:
            seen.add(key)
            result.append(track)
    return result


def track_to_dict(track: TrackRecord) -> dict[str, Any]:
    d = track.model_dump()
    d["fetched_at"] = track.fetched_at.isoformat()
    return d


def tracks_to_json(tracks: list[TrackRecord]) -> str:
    return json.dumps([track_to_dict(t) for t in tracks], ensure_ascii=False, indent=2)
