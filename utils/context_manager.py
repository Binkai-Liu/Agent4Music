"""LLM context compression and message trimming."""

from __future__ import annotations

import json
from typing import Any


class ContextManager:
    """Manage LLM context window by trimming old messages."""

    def __init__(self, max_messages: int = 30, max_tool_result_chars: int = 4000):
        self.max_messages = max_messages
        self.max_tool_result_chars = max_tool_result_chars

    def trim_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(messages) <= self.max_messages:
            return [self._truncate_message(m) for m in messages]

        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        keep = other_msgs[-(self.max_messages - len(system_msgs)) :]
        return [self._truncate_message(m) for m in system_msgs + keep]

    def _truncate_message(self, msg: dict[str, Any]) -> dict[str, Any]:
        if msg.get("role") != "tool":
            return msg
        content = msg.get("content", "")
        if len(content) > self.max_tool_result_chars:
            msg = dict(msg)
            msg["content"] = content[: self.max_tool_result_chars - 3] + "..."
        return msg

    def summarize_tool_result(self, result: Any) -> str:
        text = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
        if len(text) > self.max_tool_result_chars:
            return text[: self.max_tool_result_chars - 3] + "..."
        return text
