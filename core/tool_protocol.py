"""Standardized tool calling protocol for Agent4Music."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: Optional[str] = None

    def to_message_content(self, max_chars: int = 4000) -> str:
        if self.success:
            text = json.dumps(self.output, ensure_ascii=False) if not isinstance(self.output, str) else self.output
        else:
            text = f"Error: {self.error}"
        if len(text) > max_chars:
            text = text[: max_chars - 3] + "..."
        return text


ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


@dataclass
class ToolRegistry:
    _tools: dict[str, ToolDefinition] = field(default_factory=dict)
    _handlers: dict[str, ToolHandler] = field(default_factory=dict)

    def register(
        self,
        definition: ToolDefinition,
        handler: ToolHandler,
    ) -> None:
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def get_definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def get_openai_tools(self) -> list[dict[str, Any]]:
        return [t.to_openai_schema() for t in self._tools.values()]

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        handler = self._handlers.get(name)
        if not handler:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        try:
            return await handler(arguments)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def has_tool(self, name: str) -> bool:
        return name in self._handlers


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


def parse_tool_calls(response_tool_calls: list[Any]) -> list[ToolCall]:
    """Parse tool calls from LLM response."""
    result: list[ToolCall] = []
    for tc in response_tool_calls or []:
        args = tc.function.arguments
        if isinstance(args, str):
            args = json.loads(args)
        result.append(
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=args,
            )
        )
    return result
