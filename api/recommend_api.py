"""Music preference and playlist recommendation API."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.recommendation import (
    get_preference_tags,
    recommend_playlists,
    recommend_with_preview,
)

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


class PreferenceTrack(BaseModel):
    title: str = ""
    artists: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    genres: list[str] = Field(default_factory=list, description="曲风偏好")
    scenes: list[str] = Field(default_factory=list, description="场景偏好")
    tags: list[str] = Field(default_factory=list, description="标签偏好")
    artists: list[str] = Field(default_factory=list, description="歌手偏好")
    sources: list[str] = Field(default_factory=list, description="偏好站点 qq/netease")
    tracks: list[PreferenceTrack] = Field(default_factory=list, description="拖拽的歌曲")
    limit: int = Field(6, ge=1, le=12)
    with_preview: bool = Field(True, description="是否拉取歌单预览曲目")


@router.get("/tags")
async def list_preference_tags():
    """Get draggable preference tags for UI."""
    return {"tags": get_preference_tags()}


@router.post("/playlists")
async def recommend_playlists_api(req: RecommendRequest):
    """Recommend playlists based on dragged preferences."""
    preferences: dict[str, Any] = {
        "genres": req.genres,
        "scenes": req.scenes,
        "tags": req.tags,
        "artists": req.artists,
        "sources": req.sources,
        "tracks": [t.model_dump() for t in req.tracks],
    }

    if req.with_preview:
        results = await recommend_with_preview(preferences, limit=req.limit)
    else:
        results = recommend_playlists(preferences, limit=req.limit)

    return {
        "preferences": preferences,
        "recommendations": results,
        "count": len(results),
    }
