"""Data validation utilities."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class ComplianceConfig(BaseModel):
    block_audio_download: bool = True
    blocked_extensions: list[str] = Field(default_factory=list)
    blocked_path_patterns: list[str] = Field(default_factory=list)


def is_compliant_url(url: str, config: ComplianceConfig) -> tuple[bool, str]:
    """Check if URL is allowed under compliance rules."""
    if not url:
        return False, "Empty URL"

    parsed = urlparse(url.lower())
    path = parsed.path

    for ext in config.blocked_extensions:
        if path.endswith(ext.lower()):
            return False, f"Blocked audio extension: {ext}"

    for pattern in config.blocked_path_patterns:
        if pattern.lower() in url.lower():
            return False, f"Blocked path pattern: {pattern}"

    return True, ""


def validate_tool_args(args: dict[str, Any], required: list[str]) -> tuple[bool, str]:
    missing = [k for k in required if k not in args or args[k] is None]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, ""


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip() or "unnamed"
