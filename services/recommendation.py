"""Playlist recommendation based on user music preferences."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from services.factory import get_site_adapter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECOMMEND_PATH = PROJECT_ROOT / "config" / "recommend_playlists.json"


def load_recommend_config() -> dict[str, Any]:
    with open(RECOMMEND_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_preference_tags() -> list[dict[str, Any]]:
    return load_recommend_config().get("preference_tags", [])


def score_playlist(playlist: dict, preferences: dict[str, Any]) -> float:
    """Score playlist by overlap with user preferences."""
    genres = set(preferences.get("genres", []))
    scenes = set(preferences.get("scenes", []))
    tags = set(preferences.get("tags", []))
    artists = set(a.lower() for a in preferences.get("artists", []))
    sources = set(preferences.get("sources", []))

    score = 0.0
    playlist_genres = set(playlist.get("genres", []))
    playlist_scenes = set(playlist.get("scenes", []))
    playlist_tags = set(playlist.get("tags", []))

    genre_overlap = len(genres & playlist_genres)
    scene_overlap = len(scenes & playlist_scenes)
    tag_overlap = len(tags & playlist_tags)

    score += genre_overlap * 3.0
    score += scene_overlap * 2.0
    score += tag_overlap * 1.5

    if sources and playlist.get("source") in sources:
        score += 1.0

    pref_tracks = preferences.get("tracks", [])
    for pt in pref_tracks:
        pt_genres = set(pt.get("tags", []) + pt.get("genres", []))
        if pt_genres & playlist_genres:
            score += 2.0
        pt_artists = [a.lower() for a in pt.get("artists", [])]
        if any(a in str(playlist_tags).lower() for a in pt_artists):
            score += 1.0

    for artist in artists:
        if artist in json.dumps(playlist, ensure_ascii=False).lower():
            score += 1.5

    return score


def recommend_playlists(
    preferences: dict[str, Any],
    limit: int = 6,
    min_score: float = 0.5,
) -> list[dict[str, Any]]:
    """Rank curated playlists by user preference overlap."""
    config = load_recommend_config()
    playlists = config.get("playlists", [])

    if not any([
        preferences.get("genres"),
        preferences.get("scenes"),
        preferences.get("tags"),
        preferences.get("artists"),
        preferences.get("tracks"),
    ]):
        return sorted(
            [{**p, "score": 0, "match_reason": "热门推荐"} for p in playlists],
            key=lambda x: x.get("name", ""),
        )[:limit]

    scored = []
    for pl in playlists:
        s = score_playlist(pl, preferences)
        if s >= min_score or s > 0:
            reasons = []
            genres = set(preferences.get("genres", []))
            scenes = set(preferences.get("scenes", []))
            overlap_g = genres & set(pl.get("genres", []))
            overlap_s = scenes & set(pl.get("scenes", []))
            if overlap_g:
                reasons.append(f"曲风匹配: {', '.join(overlap_g)}")
            if overlap_s:
                reasons.append(f"场景匹配: {', '.join(overlap_s)}")
            if not reasons:
                reasons.append("综合推荐")

            scored.append({
                **pl,
                "score": round(s, 2),
                "match_reason": " · ".join(reasons),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


async def enrich_playlist_with_tracks(recommendation: dict, preview_limit: int = 5) -> dict:
    """Fetch preview tracks for a recommended playlist."""
    source = recommendation.get("source")
    playlist_id = recommendation.get("playlist_id")
    if not source or not playlist_id:
        return {**recommendation, "preview_tracks": []}

    try:
        adapter = get_site_adapter(source)
        tracks = await adapter.fetch_playlist(str(playlist_id))
        preview = []
        for t in tracks[:preview_limit]:
            preview.append({
                "title": t.title,
                "artists": t.artists,
                "cover_url": t.cover_url,
                "track_id": t.track_id,
            })
        if preview:
            return {**recommendation, "preview_tracks": preview, "total_tracks": len(tracks)}
    except Exception as e:
        pass

    # Fallback: match tracks from DB by genre tags
    try:
        from services.database import get_db
        db = await get_db()
        genres = recommendation.get("genres", [])
        all_tracks, _ = await db.query_tracks(source=source, limit=100)
        matched = []
        for t in all_tracks:
            t_tags = set(t.get("tags") or [])
            if genres and not (t_tags & set(genres)):
                title_artist = f"{t.get('title', '')} {json.dumps(t.get('artists', []))}"
                if not any(g in title_artist for g in genres):
                    continue
            matched.append(t)
            if len(matched) >= preview_limit:
                break
        if not matched and all_tracks:
            matched = all_tracks[:preview_limit]
        preview = [{
            "title": t.get("title"),
            "artists": t.get("artists", []),
            "cover_url": t.get("cover_url"),
            "track_id": t.get("track_id"),
        } for t in matched]
        return {**recommendation, "preview_tracks": preview, "total_tracks": len(matched), "preview_source": "database"}
    except Exception as e:
        return {**recommendation, "preview_tracks": [], "fetch_error": str(e)}


async def recommend_with_preview(
    preferences: dict[str, Any],
    limit: int = 6,
    preview_limit: int = 5,
) -> list[dict[str, Any]]:
    """Recommend playlists and fetch preview tracks."""
    ranked = recommend_playlists(preferences, limit=limit, min_score=0)
    enriched = []
    for rec in ranked:
        enriched.append(await enrich_playlist_with_tracks(rec, preview_limit))
    return enriched
