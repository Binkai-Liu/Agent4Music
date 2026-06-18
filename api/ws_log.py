"""WebSocket log endpoint."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from tools.log_push import EventBus

router = APIRouter()


@router.websocket("/ws/logs/{task_id}")
async def websocket_logs(websocket: WebSocket, task_id: str):
    await websocket.accept()
    bus = EventBus.get_instance()
    queue = bus.subscribe(task_id)

    history = bus.get_history(task_id)
    for event in history:
        await websocket.send_json(event)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event.to_dict())
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        bus.unsubscribe(task_id, queue)


@router.websocket("/ws/logs")
async def websocket_global_logs(websocket: WebSocket):
    await websocket.accept()
    bus = EventBus.get_instance()
    queue = bus.subscribe_global()

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event.to_dict())
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
