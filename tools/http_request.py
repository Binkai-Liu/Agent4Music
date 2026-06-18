"""HTTP request tool with compliance checks and retry."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import httpx

from core.tool_protocol import ToolResult
from tools.proxy_pool import get_proxy_pool
from utils.validator import ComplianceConfig, is_compliant_url

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_CONFIG_PATH = PROJECT_ROOT / "config" / "app_config.json"

_last_request_time: float = 0


def _load_compliance() -> ComplianceConfig:
    with open(APP_CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    return ComplianceConfig(**cfg.get("compliance", {}))


def _load_min_interval_ms() -> int:
    with open(APP_CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg.get("min_interval_ms", 1000)


async def _rate_limit() -> None:
    global _last_request_time
    import time

    min_interval = _load_min_interval_ms() / 1000.0
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < min_interval:
        await asyncio.sleep(min_interval - elapsed)
    _last_request_time = time.monotonic()


async def http_request_handler(args: dict[str, Any]) -> ToolResult:
    url = args.get("url", "")
    method = args.get("method", "GET").upper()
    headers = args.get("headers", {})
    params = args.get("params")
    body = args.get("body")
    timeout = args.get("timeout", 30)
    retry_count = args.get("retry_count", 3)

    compliance = _load_compliance()
    ok, reason = is_compliant_url(url, compliance)
    if not ok:
        return ToolResult(success=False, error=f"Compliance blocked: {reason}")

    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    merged_headers = {**default_headers, **headers}

    proxy_pool = get_proxy_pool()
    last_error = ""

    for attempt in range(retry_count):
        await _rate_limit()
        proxy = proxy_pool.get_next() if proxy_pool.enabled else None
        proxies = {"http://": proxy, "https://": proxy} if proxy else None

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=merged_headers,
                    params=params,
                    json=body if isinstance(body, dict) else None,
                    content=body if isinstance(body, str) else None,
                    proxy=proxy,
                )

                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    try:
                        data = response.json()
                    except Exception:
                        data = response.text
                else:
                    text = response.text
                    if text.startswith("{") or text.startswith("["):
                        try:
                            data = json.loads(text)
                        except Exception:
                            data = text
                    else:
                        data = text

                return ToolResult(
                    success=response.status_code < 400,
                    output={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "data": data,
                    },
                    error=None if response.status_code < 400 else f"HTTP {response.status_code}",
                )
        except Exception as e:
            last_error = str(e)
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)

    return ToolResult(success=False, error=f"Request failed after {retry_count} attempts: {last_error}")


HTTP_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "Request URL"},
        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"], "default": "GET"},
        "headers": {"type": "object", "description": "Optional HTTP headers"},
        "params": {"type": "object", "description": "Query parameters"},
        "body": {"description": "Request body (JSON object or string)"},
        "timeout": {"type": "number", "default": 30},
        "retry_count": {"type": "integer", "default": 3},
    },
    "required": ["url"],
}
