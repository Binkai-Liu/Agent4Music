#!/usr/bin/env python3
"""Single site demo: fetch hot chart from QQ or NetEase."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.database import get_db
from services.factory import get_site_adapter
from utils.banner import print_banner
from utils.logger import logger


async def main():
    print_banner()
    source = sys.argv[1] if len(sys.argv) > 1 else "qq"
    logger.info("Fetching hot chart from %s...", source)

    db = await get_db()
    task_id = await db.create_task(
        name=f"Demo hot chart - {source}",
        source=source,
        task_type="hot_chart",
        config={"limit": 20},
    )

    adapter = get_site_adapter(source)
    chart = await adapter.fetch_hot_chart(limit=20)
    count = await db.save_tracks(chart.tracks, task_id)
    await db.update_task_status(task_id, "completed", result={"track_count": count})

    logger.info("Saved %d tracks from %s (%s)", count, chart.name, source)
    for i, t in enumerate(chart.tracks[:5]):
        logger.info("  #%d %s - %s", i + 1, t.title, ", ".join(t.artists))


if __name__ == "__main__":
    asyncio.run(main())
