"""Playwright browser tool for dynamic page rendering."""

from __future__ import annotations

from typing import Any, Optional

from core.tool_protocol import ToolResult
from utils.validator import ComplianceConfig, is_compliant_url
from tools.http_request import _load_compliance

_browser = None
_playwright = None


async def _get_browser():
    global _browser, _playwright
    if _browser is None:
        from playwright.async_api import async_playwright

        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
    return _browser


async def close_browser() -> None:
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None


async def browser_handler(args: dict[str, Any]) -> ToolResult:
    url = args.get("url", "")
    wait_selector = args.get("wait_selector")
    timeout = args.get("timeout", 30000)
    extract = args.get("extract", "html")

    compliance = _load_compliance()
    ok, reason = is_compliant_url(url, compliance)
    if not ok:
        return ToolResult(success=False, error=f"Compliance blocked: {reason}")

    try:
        browser = await _get_browser()
        page = await browser.new_page()
        await page.goto(url, timeout=timeout, wait_until="networkidle")

        if wait_selector:
            await page.wait_for_selector(wait_selector, timeout=timeout)

        if extract == "text":
            content = await page.inner_text("body")
        elif extract == "json":
            content = await page.evaluate("() => document.body.innerText")
        else:
            content = await page.content()

        title = await page.title()
        await page.close()

        return ToolResult(
            success=True,
            output={"url": url, "title": title, "content": content[:50000]},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


BROWSER_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "Page URL to render"},
        "wait_selector": {"type": "string", "description": "CSS selector to wait for"},
        "timeout": {"type": "integer", "default": 30000},
        "extract": {"type": "string", "enum": ["html", "text", "json"], "default": "html"},
    },
    "required": ["url"],
}
