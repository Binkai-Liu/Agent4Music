"""Multi-provider LLM client with unified chat interface."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LLM_CONFIG_PATH = PROJECT_ROOT / "config" / "llm_config.json"


class LLMClient:
    """Unified LLM client supporting OpenAI, Anthropic, Qwen, and Ollama."""

    def __init__(self, config_path: Optional[Path] = None):
        with open(config_path or LLM_CONFIG_PATH, encoding="utf-8") as f:
            self.config = json.load(f)
        self.provider = self.config.get("provider", "openai")
        self.model = self.config.get("model", "gpt-4o-mini")
        self.temperature = self.config.get("temperature", 0.3)
        self.max_tokens = self.config.get("max_tokens", 4096)
        self._client: Any = None

    def _get_api_key(self) -> Optional[str]:
        provider_cfg = self.config.get("providers", {}).get(self.provider, {})
        env_name = provider_cfg.get("api_key_env") or self.config.get("api_key_env", "OPENAI_API_KEY")
        return os.environ.get(env_name)

    def _get_base_url(self) -> Optional[str]:
        provider_cfg = self.config.get("providers", {}).get(self.provider, {})
        return provider_cfg.get("base_url") or self.config.get("base_url")

    def _init_client(self) -> Any:
        if self._client is not None:
            return self._client

        if self.provider == "anthropic":
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._get_api_key())
        else:
            from openai import AsyncOpenAI

            kwargs: dict[str, Any] = {}
            api_key = self._get_api_key()
            if api_key:
                kwargs["api_key"] = api_key
            base_url = self._get_base_url()
            if base_url:
                kwargs["base_url"] = base_url
            if self.provider == "ollama":
                kwargs.setdefault("api_key", "ollama")
                self.model = self.config.get("providers", {}).get("ollama", {}).get("model", self.model)
            self._client = AsyncOpenAI(**kwargs)

        return self._client

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Send chat completion and return normalized response."""
        client = self._init_client()

        if self.provider == "anthropic":
            return await self._chat_anthropic(client, messages, tools)
        return await self._chat_openai(client, messages, tools)

    async def _chat_openai(
        self,
        client: Any,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments,
                }
                for tc in message.tool_calls
            ]

        return {
            "content": message.content,
            "tool_calls": tool_calls,
            "finish_reason": choice.finish_reason,
        }

    async def _chat_anthropic(
        self,
        client: Any,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]],
    ) -> dict[str, Any]:
        system = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)

        anthropic_tools = None
        if tools:
            anthropic_tools = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]

        kwargs: dict[str, Any] = {
            "model": self.model if "claude" in self.model else "claude-3-5-haiku-20241022",
            "max_tokens": self.max_tokens,
            "messages": chat_messages,
        }
        if system:
            kwargs["system"] = system
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = await client.messages.create(**kwargs)

        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })

        return {
            "content": content or None,
            "tool_calls": tool_calls,
            "finish_reason": response.stop_reason,
        }

    async def complete(self, prompt: str) -> str:
        """Simple text completion without tools."""
        result = await self.chat([{"role": "user", "content": prompt}])
        return result.get("content") or ""
