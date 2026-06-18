"""Task management API."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.schemas import MusicSource
from core.task_scheduler import get_scheduler
from services.database import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    name: str
    sources: list[str] = Field(..., min_length=1)
    task_type: str = "hot_chart"
    config: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0


class UpdatePriorityRequest(BaseModel):
    priority: int


@router.post("")
async def create_task(req: CreateTaskRequest):
    scheduler = await get_scheduler()
    task_id = await scheduler.create_task(
        name=req.name,
        sources=req.sources,
        task_type=req.task_type,
        config=req.config,
        priority=req.priority,
    )
    return {"task_id": task_id, "status": "pending"}


@router.get("")
async def list_tasks(status: Optional[str] = None, limit: int = 50):
    db = await get_db()
    tasks = await db.list_tasks(status=status, limit=limit)
    return {"tasks": tasks, "count": len(tasks)}


@router.get("/recommend/types")
async def recommend_types(source: MusicSource = MusicSource.qq):
    recommendations = {
        MusicSource.qq: ["hot_chart", "playlist", "artist"],
        MusicSource.netease: ["hot_chart", "playlist", "artist"],
    }
    return {
        "source": source.value,
        "source_label": MusicSource.labels()[source.value],
        "recommended": recommendations.get(source, ["hot_chart"]),
        "description": "根据站点特性推荐的数据采集类型",
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    db = await get_db()
    task = await db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}/pause")
async def pause_task(task_id: str):
    scheduler = await get_scheduler()
    await scheduler.pause_task(task_id)
    return {"task_id": task_id, "status": "paused"}


@router.patch("/{task_id}/resume")
async def resume_task(task_id: str):
    scheduler = await get_scheduler()
    await scheduler.resume_task(task_id)
    return {"task_id": task_id, "status": "pending"}


@router.patch("/{task_id}/cancel")
async def cancel_task(task_id: str):
    scheduler = await get_scheduler()
    await scheduler.cancel_task(task_id)
    return {"task_id": task_id, "status": "cancelled"}


@router.patch("/{task_id}/priority")
async def update_priority(task_id: str, req: UpdatePriorityRequest):
    db = await get_db()
    task = await db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "priority": req.priority}
