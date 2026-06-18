"""Skill execution engine with on-demand loading."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from services.common_parser import (
    TrackRecord,
    deduplicate_tracks,
    get_nested,
    normalize_duration,
    track_to_dict,
)
from utils.logger import logger
from utils.md_parser import load_skill_content

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GENRE_KEYWORDS = {
    "流行": ["流行", "pop", "情歌", "爱情"],
    "摇滚": ["摇滚", "rock", "金属", "朋克"],
    "古风": ["古风", "中国风", "汉服", "江湖"],
    "电子": ["电子", "edm", "电音", "dubstep"],
    "说唱": ["说唱", "rap", "hip-hop", "hiphop"],
    "民谣": ["民谣", "folk", "吉他"],
    "纯音乐": ["纯音乐", "instrumental", "钢琴", "轻音乐"],
    "R&B": ["r&b", "rnb", "节奏布鲁斯"],
}

SCENE_KEYWORDS = {
    "治愈": ["治愈", "温暖", "安静", "舒缓"],
    "热血": ["热血", "燃", "战斗", "激情"],
    "怀旧": ["怀旧", "经典", "回忆", "老歌"],
    "睡前": ["睡前", "睡眠", "摇篮", "晚安"],
    "运动": ["运动", "健身", "跑步", " workout"],
}


class SkillExecutor:
    """Execute skills on demand with SKILL.md context."""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def execute(self, skill_name: str, args: dict[str, Any]) -> dict[str, Any]:
        skill_doc = load_skill_content(skill_name)
        logger.info("Executing skill %s (doc loaded: %s)", skill_name, bool(skill_doc))

        handlers = {
            "data_clean": self._data_clean,
            "lyric_parse": self._lyric_parse,
            "tag_classify": self._tag_classify,
            "site_adapt": self._site_adapt,
        }

        handler = handlers.get(skill_name)
        if not handler:
            return {"error": f"Unknown skill: {skill_name}"}

        result = handler(args)
        if hasattr(result, "__await__"):
            result = await result

        return {"skill": skill_name, "result": result, "skill_doc_preview": (skill_doc or "")[:200]}

    def _data_clean(self, args: dict[str, Any]) -> dict[str, Any]:
        raw_data = args.get("raw_data", [])
        source = args.get("source", "unknown")
        field_mapping = args.get("field_mapping", {})

        if isinstance(raw_data, dict):
            raw_data = raw_data.get("tracks") or raw_data.get("songlist") or raw_data.get("songs") or [raw_data]

        if not field_mapping:
            rules_path = PROJECT_ROOT / "config" / "spider_rules" / f"{source}.json"
            if rules_path.exists():
                rules = json.loads(rules_path.read_text(encoding="utf-8"))
                field_mapping = rules.get("field_mapping", {})

        tracks: list[TrackRecord] = []
        for idx, item in enumerate(raw_data):
            if not isinstance(item, dict):
                continue

            track_id = str(get_nested(item, field_mapping.get("track_id", "id"), idx))
            title = get_nested(item, field_mapping.get("title", "title"), "")
            if not title:
                continue

            artist_path = field_mapping.get("artist", "artist")
            artist_val = get_nested(item, artist_path, "")
            if isinstance(artist_val, list):
                artists = [str(a.get("name", a) if isinstance(a, dict) else a) for a in artist_val]
            elif artist_val:
                artists = [str(artist_val)]
            else:
                artists = []

            album = get_nested(item, field_mapping.get("album", "album"))
            duration = normalize_duration(
                get_nested(item, field_mapping.get("duration_ms", "duration")),
                source,
            )
            play_count = get_nested(item, field_mapping.get("play_count", "play_count"))
            cover = get_nested(item, field_mapping.get("cover_url", "cover_url"))
            if cover and source == "qq" and isinstance(cover, str) and len(cover) < 20:
                cover = f"https://y.gtimg.cn/music/photo_new/T002R300x300M000{cover}.jpg"

            tracks.append(
                TrackRecord(
                    track_id=track_id,
                    source=source,
                    title=str(title),
                    artists=artists,
                    album=str(album) if album else None,
                    duration_ms=duration,
                    play_count=int(play_count) if play_count else None,
                    chart_rank=idx + 1,
                    cover_url=str(cover) if cover else None,
                )
            )

        cleaned = deduplicate_tracks(tracks)
        return {
            "count": len(cleaned),
            "tracks": [track_to_dict(t) for t in cleaned],
        }

    def _lyric_parse(self, args: dict[str, Any]) -> dict[str, Any]:
        lyric_raw = args.get("lyric_raw", "")
        if not lyric_raw:
            return {"lines": [], "plain_text": ""}

        pattern = re.compile(r"\[(\d{2}):(\d{2})(?:\.(\d{2,3}))?\](.*)")
        lines = []
        plain_parts = []

        for line in lyric_raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                mm, ss, ms, text = match.groups()
                ms_val = int(ms or 0)
                if ms and len(ms) == 2:
                    ms_val *= 10
                timestamp_ms = int(mm) * 60000 + int(ss) * 1000 + ms_val
                lines.append({"timestamp_ms": timestamp_ms, "text": text.strip()})
                if text.strip():
                    plain_parts.append(text.strip())
            elif not line.startswith("["):
                plain_parts.append(line)

        return {
            "lines": lines,
            "plain_text": "\n".join(plain_parts),
            "line_count": len(lines),
        }

    async def _tag_classify(self, args: dict[str, Any]) -> dict[str, Any]:
        title = args.get("title", "")
        artist = args.get("artist", "")
        lyric = args.get("lyric", "") or args.get("lyric_text", "")
        combined = f"{title} {artist} {lyric}".lower()

        genre_tags: list[str] = []
        scene_tags: list[str] = []

        for genre, keywords in GENRE_KEYWORDS.items():
            if any(kw.lower() in combined for kw in keywords):
                genre_tags.append(genre)

        for scene, keywords in SCENE_KEYWORDS.items():
            if any(kw.lower() in combined for kw in keywords):
                scene_tags.append(scene)

        if not genre_tags and self.llm:
            try:
                prompt = f"为歌曲分类曲风标签（仅返回JSON数组）:\n歌曲:{title}\n歌手:{artist}\n歌词片段:{lyric[:200]}"
                response = await self.llm.complete(prompt)
                import json as json_mod
                parsed = json_mod.loads(response.strip().strip("`").replace("json", ""))
                if isinstance(parsed, list):
                    genre_tags = parsed[:5]
            except Exception:
                genre_tags = ["流行"]

        if not genre_tags:
            genre_tags = ["流行"]

        return {
            "genre_tags": genre_tags,
            "scene_tags": scene_tags,
            "all_tags": genre_tags + scene_tags,
        }

    def _site_adapt(self, args: dict[str, Any]) -> dict[str, Any]:
        source = args.get("source", "qq")
        data_type = args.get("data_type", "hot_chart")
        rules_path = PROJECT_ROOT / "config" / "spider_rules" / f"{source}.json"

        if not rules_path.exists():
            return {"error": f"No rules for source: {source}"}

        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        endpoint = rules.get("endpoints", {}).get(data_type, {})

        return {
            "source": source,
            "site_name": rules.get("site_name"),
            "data_type": data_type,
            "endpoint": endpoint,
            "field_mapping": rules.get("field_mapping"),
            "rate_limit_ms": rules.get("rate_limit_ms"),
        }
