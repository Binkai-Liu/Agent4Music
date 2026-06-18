"""Task scheduler with state machine and retry."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.sub_agent import SubAgentRunner, spawn_sub_agents
from core.tool_protocol import ToolRegistry
from services.database import Database, get_db
from tools.log_push import push_log
from tools.registry import create_tool_registry
from utils.logger import logger


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    task_id: str
    sources: list[str]
    task_type: str
    config: dict[str, Any]
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3


class TaskScheduler:
    """Manage task lifecycle: pending -> running -> completed/failed."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db
        self.registry = create_tool_registry()
        self._running: dict[str, asyncio.Task] = {}
        self._paused: set[str] = set()
        self._cancelled: set[str] = set()
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._scheduler = AsyncIOScheduler()
        self._worker_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        if self.db is None:
            self.db = await get_db()
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def shutdown(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
        self._scheduler.shutdown(wait=False)

    async def create_task(
        self,
        name: str,
        sources: list[str],
        task_type: str,
        config: Optional[dict] = None,
        priority: int = 0,
    ) -> str:
        config = config or {}
        source_str = ",".join(sources)
        task_id = await self.db.create_task(name, source_str, task_type, config, priority)

        scheduled = ScheduledTask(
            task_id=task_id,
            sources=sources,
            task_type=task_type,
            config=config,
            priority=priority,
        )
        await self._queue.put((-priority, scheduled))
        await push_log(task_id, "task_created", f"Task created: {name}", {"sources": sources})

        return task_id

    async def pause_task(self, task_id: str) -> bool:
        self._paused.add(task_id)
        await self.db.update_task_status(task_id, TaskStatus.PAUSED.value)
        await push_log(task_id, "task_paused", "Task paused")
        return True

    async def resume_task(self, task_id: str) -> bool:
        self._paused.discard(task_id)
        task = await self.db.get_task(task_id)
        if task:
            scheduled = ScheduledTask(
                task_id=task_id,
                sources=task["source"].split(","),
                task_type=task["task_type"],
                config=task.get("config", {}),
            )
            await self._queue.put((0, scheduled))
            await self.db.update_task_status(task_id, TaskStatus.PENDING.value)
            await push_log(task_id, "task_resumed", "Task resumed")
        return True

    async def cancel_task(self, task_id: str) -> bool:
        self._cancelled.add(task_id)
        if task_id in self._running:
            self._running[task_id].cancel()
        await self.db.update_task_status(task_id, TaskStatus.CANCELLED.value)
        await push_log(task_id, "task_cancelled", "Task cancelled")
        return True

    def schedule_cron(
        self,
        name: str,
        sources: list[str],
        task_type: str,
        cron: str,
        config: Optional[dict] = None,
    ) -> None:
        parts = cron.split()
        trigger = CronTrigger(
            minute=parts[0] if len(parts) > 0 else "*",
            hour=parts[1] if len(parts) > 1 else "*",
            day=parts[2] if len(parts) > 2 else "*",
            month=parts[3] if len(parts) > 3 else "*",
            day_of_week=parts[4] if len(parts) > 4 else "*",
        )

        async def job():
            await self.create_task(name, sources, task_type, config)

        self._scheduler.add_job(job, trigger, id=f"cron_{name}")
        if not self._scheduler.running:
            self._scheduler.start()

    async def _worker_loop(self) -> None:
        while True:
            try:
                _, scheduled = await self._queue.get()
                if scheduled.task_id in self._cancelled:
                    continue
                while scheduled.task_id in self._paused:
                    await asyncio.sleep(1)
                    if scheduled.task_id in self._cancelled:
                        break
                else:
                    await self._execute_task(scheduled)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Worker loop error: %s", e)
                await asyncio.sleep(1)

    async def _execute_task(self, scheduled: ScheduledTask) -> None:
        task_id = scheduled.task_id
        await self.db.update_task_status(task_id, TaskStatus.RUNNING.value)
        await push_log(task_id, "task_start", f"Executing {scheduled.task_type}", {"sources": scheduled.sources})

        try:
            if len(scheduled.sources) > 1:
                results = await spawn_sub_agents(
                    task_id,
                    scheduled.sources,
                    {"task_type": scheduled.task_type, **scheduled.config},
                    self.registry,
                    self.db,
                )
                success = all(r.success for r in results)
                result_data = [{"source": r.source, "success": r.success, "data": r.data, "error": r.error} for r in results]
            else:
                runner = SubAgentRunner(self.registry, self.db)
                result = await runner.run_site_task(
                    task_id,
                    scheduled.sources[0],
                    scheduled.task_type,
                    scheduled.config,
                )
                success = result.success
                result_data = {"source": result.source, "data": result.data, "error": result.error}

            if success:
                await self.db.update_task_status(task_id, TaskStatus.COMPLETED.value, result=result_data)
                await push_log(task_id, "task_complete", "Task completed successfully", result_data)
            else:
                await self._handle_failure(scheduled, str(result_data))

        except asyncio.CancelledError:
            await self.db.update_task_status(task_id, TaskStatus.CANCELLED.value)
        except Exception as e:
            logger.exception("Task execution failed: %s", e)
            await self._handle_failure(scheduled, str(e))

    async def _handle_failure(self, scheduled: ScheduledTask, error: str) -> None:
        scheduled.retry_count += 1
        if scheduled.retry_count <= scheduled.max_retries:
            delay = 2 ** scheduled.retry_count
            await push_log(
                scheduled.task_id,
                "task_retry",
                f"Retry {scheduled.retry_count}/{scheduled.max_retries} in {delay}s",
                {"error": error},
            )
            await asyncio.sleep(delay)
            await self._queue.put((-scheduled.priority, scheduled))
        else:
            await self.db.update_task_status(scheduled.task_id, TaskStatus.FAILED.value, error=error)
            await push_log(scheduled.task_id, "task_failed", error, {"retries": scheduled.retry_count})


_scheduler_instance: Optional[TaskScheduler] = None


async def get_scheduler() -> TaskScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
        await _scheduler_instance.initialize()
    return _scheduler_instance
