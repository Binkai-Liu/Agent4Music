#!/usr/bin/env python3
"""Skill demo: test data_clean, lyric_parse, tag_classify."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skills.executor import SkillExecutor
from utils.banner import print_banner
from utils.logger import logger


async def main():
    print_banner()
    executor = SkillExecutor()

    raw_data = [
        {"songmid": "001", "songname": "七里香", "singer": [{"name": "周杰伦"}], "albumname": "七里香", "interval": 240},
        {"songmid": "002", "songname": "晴天", "singer": [{"name": "周杰伦"}], "albumname": "叶惠美", "interval": 269},
    ]

    clean_result = await executor.execute("data_clean", {"raw_data": raw_data, "source": "qq"})
    logger.info("data_clean: %d tracks", clean_result["result"]["count"])

    lyric = "[00:12.00]窗外的麻雀 在电线杆上多嘴\n[00:18.00]你说这一句 很有夏天的感觉"
    lyric_result = await executor.execute("lyric_parse", {"lyric_raw": lyric})
    logger.info("lyric_parse: %s", lyric_result["result"]["plain_text"][:50])

    tag_result = await executor.execute("tag_classify", {
        "title": "七里香",
        "artist": "周杰伦",
        "lyric": "窗外的麻雀",
    })
    logger.info("tag_classify: %s", tag_result["result"]["all_tags"])

    site_result = await executor.execute("site_adapt", {"source": "qq", "data_type": "hot_chart"})
    logger.info("site_adapt: %s", site_result["result"].get("endpoint", {}).get("url", ""))


if __name__ == "__main__":
    asyncio.run(main())
