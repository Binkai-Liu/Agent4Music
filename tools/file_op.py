"""File read/write and data export tool."""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from core.tool_protocol import ToolResult
from utils.validator import sanitize_filename

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


async def file_op_handler(args: dict[str, Any]) -> ToolResult:
    action = args.get("action", "read")
    path = args.get("path", "")
    content = args.get("content")
    format_type = args.get("format", "json")

    if not path:
        return ToolResult(success=False, error="path is required")

    file_path = _resolve_path(sanitize_filename(path) if "/" not in path and "\\" not in path else path)

    try:
        if action == "read":
            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {file_path}")
            text = file_path.read_text(encoding="utf-8")
            if format_type == "json":
                data = json.loads(text)
            else:
                data = text
            return ToolResult(success=True, output={"path": str(file_path), "data": data})

        if action == "write":
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if format_type == "json":
                file_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
            elif format_type == "csv" and isinstance(content, list):
                if content:
                    df = pd.DataFrame(content)
                    df.to_csv(file_path, index=False, encoding="utf-8-sig")
                else:
                    file_path.write_text("", encoding="utf-8")
            elif format_type == "xlsx" and isinstance(content, list):
                df = pd.DataFrame(content)
                df.to_excel(file_path, index=False)
            else:
                file_path.write_text(str(content), encoding="utf-8")
            return ToolResult(success=True, output={"path": str(file_path), "written": True})

        if action == "list":
            if not file_path.exists():
                return ToolResult(success=False, error=f"Directory not found: {file_path}")
            files = [f.name for f in file_path.iterdir()]
            return ToolResult(success=True, output={"files": files})

        return ToolResult(success=False, error=f"Unknown action: {action}")
    except Exception as e:
        return ToolResult(success=False, error=str(e))


FILE_OP_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["read", "write", "list"], "description": "File operation"},
        "path": {"type": "string", "description": "File or directory path"},
        "content": {"description": "Content to write (for write action)"},
        "format": {"type": "string", "enum": ["json", "csv", "xlsx", "text"], "default": "json"},
    },
    "required": ["action", "path"],
}
