"""ECharts chart data assembly."""

from __future__ import annotations

from typing import Any


def build_stats_charts(stats: dict[str, Any]) -> dict[str, Any]:
    by_source = stats.get("by_source", {})
    by_tags = stats.get("by_tags", {})

    return {
        "source_bar": {
            "title": "站点数据分布",
            "xAxis": list(by_source.keys()),
            "series": [{"name": "歌曲数", "data": list(by_source.values())}],
        },
        "genre_pie": {
            "title": "曲风占比",
            "data": [{"name": k, "value": v} for k, v in by_tags.items()],
        },
        "summary": {
            "total_tracks": stats.get("total_tracks", 0),
            "total_tasks": stats.get("total_tasks", 0),
            "running_tasks": stats.get("running_tasks", 0),
        },
    }


def build_task_flow_mermaid(task_id: str, events: list[dict]) -> str:
    lines = ["flowchart LR"]
    prev = "Start"
    lines.append(f"    Start[任务 {task_id[:8]}]")
    for i, ev in enumerate(events[:10]):
        node = f"N{i}"
        label = ev.get("event_type", "event").replace("_", " ")
        lines.append(f"    {prev} --> {node}[{label}]")
        prev = node
    lines.append(f"    {prev} --> End[完成]")
    return "\n".join(lines)
