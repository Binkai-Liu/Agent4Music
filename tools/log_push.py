"""WebSocket log push and event bus."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


@dataclass
class LogEvent:
    task_id: str
    event_type: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "event_type": self.event_type,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class EventBus:
    """In-memory event bus for log push and WebSocket consumption."""

    _instance: Optional["EventBus"] = None

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._global_subscribers: list[asyncio.Queue] = []
        self._history: dict[str, list[LogEvent]] = defaultdict(list)
        self._max_history = 500

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def publish(self, event: LogEvent) -> None:
        self._history[event.task_id].append(event)
        if len(self._history[event.task_id]) > self._max_history:
            self._history[event.task_id] = self._history[event.task_id][-self._max_history:]

        for queue in self._subscribers.get(event.task_id, []):
            await queue.put(event)
        for queue in self._global_subscribers:
            await queue.put(event)

    def subscribe(self, task_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[task_id].append(queue)
        return queue

    def subscribe_global(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._global_subscribers.append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        if task_id in self._subscribers and queue in self._subscribers[task_id]:
            self._subscribers[task_id].remove(queue)

    def get_history(self, task_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._history.get(task_id, [])[-limit:]]


async def push_log(task_id: str, event_type: str, message: str, data: Optional[dict] = None) -> LogEvent:
    event = LogEvent(task_id=task_id, event_type=event_type, message=message, data=data or {})
    await EventBus.get_instance().publish(event)
    return event
