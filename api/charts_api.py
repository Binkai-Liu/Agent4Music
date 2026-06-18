"""Latest charts API."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.schemas import ChartType, MusicSource
from services.chart_service import fetch_all_latest, fetch_latest_chart, list_charts
from services.database import get_db

router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.get("/catalog")
async def get_charts_catalog(source: Optional[MusicSource] = None):
    """List all available chart types."""
    return {"charts": list_charts(source.value if source else None)}


@router.get("/sites")
async def get_site_options():
    """Site options for frontend selects."""
    return {
        "sites": [
            {"value": s.value, "label": MusicSource.labels()[s.value]}
            for s in MusicSource
        ],
        "default": MusicSource.qq.value,
    }


@router.get("/latest")
async def get_latest_chart(
    source: MusicSource = Query(MusicSource.qq, description="音乐站点"),
    chart_type: ChartType = Query(ChartType.hot, description="榜单类型"),
    limit: int = Query(50, le=100),
    save: bool = Query(False, description="Save tracks to database"),
):
    """Fetch live latest chart from music site."""
    try:
        chart = await fetch_latest_chart(source.value, chart_type.value, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {e}")

    task_id = None
    if save and chart.tracks:
        db = await get_db()
        task_id = await db.create_task(
            name=f"Latest {chart.name}",
            source=source.value,
            task_type=f"chart_{chart_type.value}",
            config={"chart_type": chart_type.value, "limit": limit},
        )
        await db.save_tracks(chart.tracks, task_id)
        await db.update_task_status(task_id, "completed", result={"track_count": len(chart.tracks)})

    return {
        "chart_id": chart.chart_id,
        "name": chart.name,
        "source": chart.source,
        "chart_type": chart_type.value,
        "track_count": len(chart.tracks),
        "tracks": [t.model_dump(mode="json") for t in chart.tracks],
        "fetched_at": chart.fetched_at.isoformat(),
        "saved_task_id": task_id,
    }


@router.get("/latest/all")
async def get_all_latest_charts(
    source: MusicSource = Query(MusicSource.qq, description="音乐站点"),
    limit: int = Query(20, le=50),
):
    """Fetch all chart types for a source."""
    try:
        results = await fetch_all_latest(source.value, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"source": source.value, "charts": results}
