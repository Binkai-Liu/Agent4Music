"""Sub-agent for parallel single-site crawling."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Optional

from core.agent_loop import AgentEvent, AgentLoop, AgentLoopResult
from core.llm_client import LLMClient
from core.tool_protocol import ToolRegistry
from services.chart_service import fetch_latest_chart
from services.database import Database
from services.factory import get_site_adapter
from skills.executor import SkillExecutor
from tools.log_push import push_log
from utils.logger import logger

SUB_AGENT_PROMPT = """# 音乐采集子Agent 隔离规则
你是独立子智能体，拥有独立上下文，仅负责【单一音乐站点】的数据采集任务。
无法访问其他子Agent、主Agent的任务数据，任务完成后自动结束会话。
严格使用分配的站点规则执行采集，出现异常直接上报，不跨站点操作。
当前分配站点: {source}
任务类型: {task_type}
"""


@dataclass
class SubAgentResult:
    session_id: str
    source: str
    success: bool
    summary: str
    data: Any = None
    error: Optional[str] = None


class SubAgentRunner:
    """Run isolated sub-agents for single-site tasks."""

    def __init__(
        self,
        registry: ToolRegistry,
        db: Database,
        llm: Optional[LLMClient] = None,
    ):
        self.registry = registry
        self.db = db
        self.llm = llm or LLMClient()
        self.skill_executor = SkillExecutor(self.llm)

    async def run_site_task(
        self,
        task_id: str,
        source: str,
        task_type: str,
        config: dict[str, Any],
    ) -> SubAgentResult:
        session_id = str(uuid.uuid4())[:8]
        await push_log(task_id, "sub_agent_start", f"Sub-agent started for {source}", {"session_id": session_id})

        try:
            adapter = get_site_adapter(source)
            result_data: Any = None

            if task_type == "hot_chart":
                limit = config.get("limit", 50)
                chart_type = config.get("chart_type", "hot")
                chart = await fetch_latest_chart(source, chart_type, limit)
                await self.db.save_tracks(chart.tracks, task_id)
                result_data = {
                    "chart": chart.name,
                    "chart_type": chart_type,
                    "track_count": len(chart.tracks),
                }

            elif task_type == "chart":
                limit = config.get("limit", 50)
                chart_type = config.get("chart_type", "hot")
                chart = await fetch_latest_chart(source, chart_type, limit)
                await self.db.save_tracks(chart.tracks, task_id)
                result_data = {
                    "chart": chart.name,
                    "chart_type": chart_type,
                    "track_count": len(chart.tracks),
                }

            elif task_type == "playlist":
                playlist_id = config.get("playlist_id", "")
                tracks = await adapter.fetch_playlist(playlist_id)
                await self.db.save_tracks(tracks, task_id)
                result_data = {"playlist_id": playlist_id, "track_count": len(tracks)}

            elif task_type == "artist":
                artist_id = config.get("artist_id", "")
                artist = await adapter.fetch_artist(artist_id)
                await self.db.save_artist(artist, task_id)
                result_data = {"artist": artist.name, "artist_id": artist_id}

            else:
                return SubAgentResult(
                    session_id=session_id,
                    source=source,
                    success=False,
                    summary="",
                    error=f"Unknown task type: {task_type}",
                )

            summary = f"Completed {task_type} for {source}: {result_data}"
            await push_log(task_id, "sub_agent_finish", summary, result_data)

            return SubAgentResult(
                session_id=session_id,
                source=source,
                success=True,
                summary=summary,
                data=result_data,
            )

        except Exception as e:
            logger.exception("Sub-agent failed for %s", source)
            await push_log(task_id, "sub_agent_error", str(e), {"source": source})
            return SubAgentResult(
                session_id=session_id,
                source=source,
                success=False,
                summary="",
                error=str(e),
            )

    async def spawn_parallel(
        self,
        task_id: str,
        sites: list[str],
        task_type: str,
        config: dict[str, Any],
    ) -> list[SubAgentResult]:
        tasks = [
            self.run_site_task(task_id, source, task_type, config)
            for source in sites
        ]
        return await asyncio.gather(*tasks)


async def spawn_sub_agents(
    task_id: str,
    site_list: list[str],
    task_config: dict[str, Any],
    registry: ToolRegistry,
    db: Database,
) -> list[SubAgentResult]:
    runner = SubAgentRunner(registry, db)
    return await runner.spawn_parallel(
        task_id,
        site_list,
        task_config.get("task_type", "hot_chart"),
        task_config,
    )
