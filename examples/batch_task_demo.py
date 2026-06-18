#!/usr/bin/env python3
"""Batch task demo: parallel fetch from QQ and NetEase."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.task_scheduler import get_scheduler
from services.database import get_db
from utils.banner import print_banner
from utils.logger import logger


async def main():
    print_banner()
    db = await get_db()
    scheduler = await get_scheduler()

    task_id = await scheduler.create_task(
        name="Batch dual-site hot chart",
        sources=["qq", "netease"],
        task_type="hot_chart",
        config={"limit": 30},
        priority=10,
    )

    logger.info("Created batch task: %s", task_id)
    logger.info("Waiting for completion...")

    for _ in range(60):
        await asyncio.sleep(2)
        task = await db.get_task(task_id)
        if task and task["status"] in ("completed", "failed", "cancelled"):
            logger.info("Task finished: status=%s result=%s", task["status"], task.get("result"))
            break
    else:
        logger.warning("Task still running after timeout")


if __name__ == "__main__":
    asyncio.run(main())
