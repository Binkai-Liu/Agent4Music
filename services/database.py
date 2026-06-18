"""SQLite persistence layer."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from services.common_parser import ArtistRecord, ChartRecord, TrackRecord, track_to_dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = PROJECT_ROOT / "data" / "music_db.db"


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    source TEXT,
                    task_type TEXT,
                    status TEXT DEFAULT 'pending',
                    config TEXT,
                    result TEXT,
                    error TEXT,
                    priority INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    started_at TEXT,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id TEXT,
                    source TEXT,
                    title TEXT,
                    artists TEXT,
                    album TEXT,
                    duration_ms INTEGER,
                    play_count INTEGER,
                    chart_rank INTEGER,
                    tags TEXT,
                    lyric_raw TEXT,
                    cover_url TEXT,
                    task_id TEXT,
                    fetched_at TEXT,
                    UNIQUE(track_id, source, task_id)
                );

                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist_id TEXT,
                    source TEXT,
                    name TEXT,
                    description TEXT,
                    avatar_url TEXT,
                    track_count INTEGER,
                    task_id TEXT,
                    fetched_at TEXT
                );

                CREATE TABLE IF NOT EXISTS charts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chart_id TEXT,
                    source TEXT,
                    name TEXT,
                    track_count INTEGER,
                    task_id TEXT,
                    fetched_at TEXT
                );

                CREATE TABLE IF NOT EXISTS raw_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE,
                    source TEXT,
                    data TEXT,
                    created_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_tracks_source ON tracks(source);
                CREATE INDEX IF NOT EXISTS idx_tracks_task ON tracks(task_id);
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            """)
            await db.commit()

    async def create_task(
        self,
        name: str,
        source: str,
        task_type: str,
        config: dict,
        priority: int = 0,
    ) -> str:
        task_id = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO tasks (id, name, source, task_type, status, config, priority, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
                (task_id, name, source, task_type, json.dumps(config), priority, now, now),
            )
            await db.commit()
        return task_id

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            fields = ["status = ?", "updated_at = ?"]
            values: list[Any] = [status, now]

            if status == "running":
                fields.append("started_at = ?")
                values.append(now)
            if status in ("completed", "failed", "cancelled"):
                fields.append("completed_at = ?")
                values.append(now)
            if result is not None:
                fields.append("result = ?")
                values.append(json.dumps(result, ensure_ascii=False))
            if error:
                fields.append("error = ?")
                values.append(error)

            values.append(task_id)
            await db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)
            await db.commit()

    async def get_task(self, task_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
        return None

    async def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                query = "SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at DESC LIMIT ?"
                params = (status, limit)
            else:
                query = "SELECT * FROM tasks ORDER BY priority DESC, created_at DESC LIMIT ?"
                params = (limit,)
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_dict(r) for r in rows]

    async def save_tracks(self, tracks: list[TrackRecord], task_id: str) -> int:
        count = 0
        async with aiosqlite.connect(self.db_path) as db:
            for track in tracks:
                try:
                    await db.execute(
                        """INSERT OR REPLACE INTO tracks
                           (track_id, source, title, artists, album, duration_ms, play_count,
                            chart_rank, tags, lyric_raw, cover_url, task_id, fetched_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            track.track_id,
                            track.source,
                            track.title,
                            json.dumps(track.artists, ensure_ascii=False),
                            track.album,
                            track.duration_ms,
                            track.play_count,
                            track.chart_rank,
                            json.dumps(track.tags, ensure_ascii=False),
                            track.lyric_raw,
                            track.cover_url,
                            task_id,
                            track.fetched_at.isoformat(),
                        ),
                    )
                    count += 1
                except Exception:
                    pass
            await db.commit()
        return count

    async def save_artist(self, artist: ArtistRecord, task_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO artists (artist_id, source, name, description, avatar_url, track_count, task_id, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    artist.artist_id,
                    artist.source,
                    artist.name,
                    artist.description,
                    artist.avatar_url,
                    artist.track_count,
                    task_id,
                    artist.fetched_at.isoformat(),
                ),
            )
            await db.commit()

    async def query_tracks(
        self,
        source: Optional[str] = None,
        search: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        conditions = []
        params: list[Any] = []

        if source:
            conditions.append("source = ?")
            params.append(source)
        if task_id:
            conditions.append("task_id = ?")
            params.append(task_id)
        if search:
            conditions.append("(title LIKE ? OR artists LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            count_query = f"SELECT COUNT(*) FROM tracks {where}"
            async with db.execute(count_query, params) as cursor:
                total = (await cursor.fetchone())[0]

            query = f"SELECT * FROM tracks {where} ORDER BY chart_rank ASC, fetched_at DESC LIMIT ? OFFSET ?"
            async with db.execute(query, params + [limit, offset]) as cursor:
                rows = await cursor.fetchall()
                return [self._track_row_to_dict(r) for r in rows], total

    async def get_stats(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            async with db.execute("SELECT COUNT(*) FROM tracks") as c:
                stats["total_tracks"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM tasks") as c:
                stats["total_tasks"] = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM tasks WHERE status = 'running'") as c:
                stats["running_tasks"] = (await c.fetchone())[0]
            async with db.execute("SELECT source, COUNT(*) as cnt FROM tracks GROUP BY source") as c:
                stats["by_source"] = {row[0]: row[1] async for row in c}
            async with db.execute(
                "SELECT tags, COUNT(*) as cnt FROM tracks WHERE tags != '[]' GROUP BY tags LIMIT 20"
            ) as c:
                tag_rows = await c.fetchall()
                stats["by_tags"] = {}
                for row in tag_rows:
                    try:
                        tags = json.loads(row[0])
                        for t in tags:
                            stats["by_tags"][t] = stats["by_tags"].get(t, 0) + 1
                    except Exception:
                        pass
            return stats

    def _row_to_dict(self, row: aiosqlite.Row) -> dict:
        d = dict(row)
        if d.get("config"):
            d["config"] = json.loads(d["config"])
        if d.get("result"):
            try:
                d["result"] = json.loads(d["result"])
            except Exception:
                pass
        return d

    def _track_row_to_dict(self, row: aiosqlite.Row) -> dict:
        d = dict(row)
        for field in ("artists", "tags"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    d[field] = []
        return d


_db_instance: Optional[Database] = None


async def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        await _db_instance.init()
    return _db_instance
