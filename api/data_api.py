"""Data query and export API."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from api.schemas import MusicSource
from services.database import get_db
from visual.chart_data import build_stats_charts

router = APIRouter(prefix="/api", tags=["data"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPORT_DIR = PROJECT_ROOT / "data" / "export"


@router.get("/data/tracks")
async def query_tracks(
    source: Optional[MusicSource] = None,
    search: Optional[str] = None,
    task_id: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    db = await get_db()
    tracks, total = await db.query_tracks(source=source.value if source else None, search=search, task_id=task_id, limit=limit, offset=offset)
    return {"tracks": tracks, "total": total, "limit": limit, "offset": offset}


@router.get("/data/charts")
async def query_charts(source: Optional[MusicSource] = None):
    db = await get_db()
    tracks, _ = await db.query_tracks(source=source.value if source else None, limit=100)
    charts = {}
    for t in tracks:
        key = f"{t.get('source')}_chart"
        if key not in charts:
            charts[key] = {"source": t.get("source"), "tracks": []}
        charts[key]["tracks"].append(t)
    return {"charts": list(charts.values())}


@router.get("/data/artists")
async def query_artists(source: Optional[MusicSource] = None, limit: int = 50):
    db = await get_db()
    async with __import__("aiosqlite").connect(db.db_path) as conn:
        conn.row_factory = __import__("aiosqlite").Row
        query = "SELECT * FROM artists"
        params = []
        if source:
            query += " WHERE source = ?"
            params.append(source.value)
        query += " ORDER BY fetched_at DESC LIMIT ?"
        params.append(limit)
        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            artists = [dict(r) for r in rows]
    return {"artists": artists, "count": len(artists)}


@router.get("/stats")
async def get_stats():
    db = await get_db()
    stats = await db.get_stats()
    charts = build_stats_charts(stats)
    return {"stats": stats, "charts": charts}


@router.get("/export")
async def export_data(
    format: str = Query("csv", pattern="^(csv|json|xlsx)$"),
    source: Optional[MusicSource] = None,
    task_id: Optional[str] = None,
):
    db = await get_db()
    tracks, _ = await db.query_tracks(source=source.value if source else None, task_id=task_id, limit=10000)

    if not tracks:
        raise HTTPException(status_code=404, detail="No data to export")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"export_{source.value if source else 'all'}_{task_id or 'all'}.{format}"
    filepath = EXPORT_DIR / filename

    if format == "json":
        filepath.write_text(json.dumps(tracks, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        df = pd.DataFrame(tracks)
        if format == "csv":
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(filepath, index=False)

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )
