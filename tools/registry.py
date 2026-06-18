"""Register all native tools into ToolRegistry."""

from __future__ import annotations

from core.tool_protocol import ToolDefinition, ToolRegistry
from tools.browser import BROWSER_SCHEMA, browser_handler
from tools.file_op import FILE_OP_SCHEMA, file_op_handler
from tools.http_request import HTTP_REQUEST_SCHEMA, http_request_handler
from tools.log_push import push_log
from tools.proxy_pool import get_proxy_pool
from core.tool_protocol import ToolResult


async def log_push_handler(args: dict) -> ToolResult:
    task_id = args.get("task_id", "default")
    event_type = args.get("event_type", "info")
    message = args.get("message", "")
    data = args.get("data", {})
    await push_log(task_id, event_type, message, data)
    return ToolResult(success=True, output={"pushed": True})


async def proxy_pool_handler(args: dict) -> ToolResult:
    pool = get_proxy_pool()
    action = args.get("action", "get")

    if action == "enable":
        pool.enable()
        return ToolResult(success=True, output={"enabled": True, "count": len(pool.list_proxies())})
    if action == "disable":
        pool.disable()
        return ToolResult(success=True, output={"enabled": False})
    if action == "add":
        proxy = args.get("proxy", "")
        if proxy:
            pool.add_proxy(proxy)
        return ToolResult(success=True, output={"proxies": pool.list_proxies()})
    if action == "get":
        proxy = pool.get_next()
        return ToolResult(success=True, output={"proxy": proxy, "enabled": pool.enabled})

    return ToolResult(success=False, error=f"Unknown action: {action}")


async def finish_handler(args: dict) -> ToolResult:
    return ToolResult(success=True, output={"summary": args.get("summary", ""), "data": args.get("data")})


async def skill_handler(args: dict) -> ToolResult:
    return ToolResult(success=True, output={"skill": args.get("skill"), "args": args.get("args"), "delegated": True})


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="http_request",
            description="Make HTTP requests to fetch public music site APIs. Respects rate limits and compliance rules.",
            parameters=HTTP_REQUEST_SCHEMA,
        ),
        http_request_handler,
    )

    registry.register(
        ToolDefinition(
            name="browser",
            description="Render dynamic JavaScript pages using headless browser. Use when API is unavailable.",
            parameters=BROWSER_SCHEMA,
        ),
        browser_handler,
    )

    registry.register(
        ToolDefinition(
            name="file_op",
            description="Read, write, or list files. Export data as JSON, CSV, or Excel.",
            parameters=FILE_OP_SCHEMA,
        ),
        file_op_handler,
    )

    registry.register(
        ToolDefinition(
            name="proxy_pool",
            description="Manage proxy rotation for anti-ban. Actions: enable, disable, add, get.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["enable", "disable", "add", "get"]},
                    "proxy": {"type": "string", "description": "Proxy URL for add action"},
                },
                "required": ["action"],
            },
        ),
        proxy_pool_handler,
    )

    registry.register(
        ToolDefinition(
            name="log_push",
            description="Push log events to WebUI in real-time.",
            parameters={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "event_type": {"type": "string"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
                "required": ["task_id", "message"],
            },
        ),
        log_push_handler,
    )

    registry.register(
        ToolDefinition(
            name="skill",
            description="Invoke a domain skill (data_clean, lyric_parse, tag_classify, site_adapt).",
            parameters={
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "Skill name"},
                    "args": {"type": "object", "description": "Skill arguments"},
                },
                "required": ["skill", "args"],
            },
        ),
        skill_handler,
    )

    registry.register(
        ToolDefinition(
            name="finish",
            description="Mark task as complete and provide summary.",
            parameters={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "data": {"description": "Final task output data"},
                },
                "required": ["summary"],
            },
        ),
        finish_handler,
    )

    return registry
