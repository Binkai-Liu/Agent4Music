"""Agent main loop with four-step handshake protocol."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from core.llm_client import LLMClient
from core.tool_protocol import ToolCall, ToolRegistry, ToolResult
from utils.context_manager import ContextManager
from utils.logger import logger
from utils.md_parser import scan_skills

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT_TEMPLATE = """# Agent4Music 系统运行规则

## 定位
你是面向音乐站点公开数据采集的智能Agent，严格遵循【模型决策，宿主执行】原则，仅负责分析、选择工具/技能，不直接执行网络请求、文件操作等动作。

## 一、工具调用规则
1. 可用工具：http_request（网络请求）、browser（动态页面渲染）、file_op（文件读写/导出）、proxy_pool（代理切换）、skill（领域技能）、finish（任务完成）。
2. 必须使用结构化工具调用格式，禁止自由文本编写指令。
3. 遇到请求失败、403、超时，自动选择重试或切换代理工具。

## 二、Skill 技能规则（按需加载）
1. 系统内置技能列表：{skills_list}
2. 所有技能共用同一个「skill」工具，调用格式：{{"skill":"技能名","args":{{...}}}}
3. 仅在原始数据格式混乱、需要解析/分类时调用技能。

## 三、业务规则（音乐场景专属）
1. 优先识别目标音乐站点，匹配对应解析规则；优先采集公开榜单、热门歌单、公开艺人信息。
2. 严格遵守合规要求：不爬取版权音频、不高频请求、不破解付费内容。
3. 多站点任务优先使用子Agent并行执行，提升效率。

## 四、终止条件
1. 所有采集、处理、入库流程完成后，调用 finish 工具输出任务总结；
2. 连续多次请求失败、站点不可访问时，调用 finish 并上报异常。

## 五、可视化要求
你的每一次工具/技能调用都会被实时推送至WebUI与终端，请保证逻辑连贯、链路清晰。
"""


@dataclass
class AgentEvent:
    event_type: str
    data: dict[str, Any]
    session_id: str = ""


@dataclass
class AgentLoopResult:
    success: bool
    summary: str
    rounds: int
    tool_calls_count: int
    data: Any = None
    error: Optional[str] = None


EventCallback = Callable[[AgentEvent], None]


@dataclass
class AgentLoop:
    llm: LLMClient
    registry: ToolRegistry
    max_rounds: int = 20
    context_manager: ContextManager = field(default_factory=ContextManager)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    on_event: Optional[EventCallback] = None
    skill_executor: Optional[Callable[[str, dict[str, Any]], Any]] = None
    extra_system: str = ""

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        if self.on_event:
            self.on_event(AgentEvent(event_type=event_type, data=data, session_id=self.session_id))

    def _build_system_prompt(self) -> str:
        skills = scan_skills()
        skills_list = ", ".join(f"{s['name']}({s['description']})" for s in skills)
        prompt = SYSTEM_PROMPT_TEMPLATE.format(skills_list=skills_list)
        if self.extra_system:
            prompt += f"\n\n{self.extra_system}"
        return prompt

    async def run(self, user_task: str) -> AgentLoopResult:
        """Execute agent loop until finish or max rounds."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_task},
        ]

        tool_calls_count = 0
        rounds = 0
        final_data: Any = None

        self._emit("agent_start", {"task": user_task, "session_id": self.session_id})

        for round_num in range(1, self.max_rounds + 1):
            rounds = round_num
            self._emit("round_start", {"round": round_num})

            messages = self.context_manager.trim_messages(messages)
            tools = self.registry.get_openai_tools()

            try:
                response = await self.llm.chat(messages, tools=tools)
            except Exception as e:
                logger.error("LLM call failed: %s", e)
                self._emit("error", {"message": str(e)})
                return AgentLoopResult(
                    success=False,
                    summary="",
                    rounds=rounds,
                    tool_calls_count=tool_calls_count,
                    error=str(e),
                )

            if response.get("content") and not response.get("tool_calls"):
                messages.append({"role": "assistant", "content": response["content"]})

            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                if response.get("finish_reason") == "stop":
                    summary = response.get("content") or "Task completed"
                    self._emit("agent_finish", {"summary": summary})
                    return AgentLoopResult(
                        success=True,
                        summary=summary,
                        rounds=rounds,
                        tool_calls_count=tool_calls_count,
                        data=final_data,
                    )
                continue

            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response.get("content")}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_msg)

            for tc in tool_calls:
                tool_calls_count += 1
                name = tc["name"]
                args = tc["arguments"]

                self._emit("tool_call", {"tool": name, "args": args, "round": round_num})

                if name == "finish":
                    summary = args.get("summary", "Task completed")
                    final_data = args.get("data")
                    self._emit("agent_finish", {"summary": summary})
                    return AgentLoopResult(
                        success=True,
                        summary=summary,
                        rounds=rounds,
                        tool_calls_count=tool_calls_count,
                        data=final_data,
                    )

                if name == "skill" and self.skill_executor:
                    skill_name = args.get("skill", "")
                    skill_args = args.get("args", {})
                    self._emit("skill_call", {"skill": skill_name, "args": skill_args})
                    try:
                        result_output = await self._execute_skill(skill_name, skill_args)
                        result = ToolResult(success=True, output=result_output)
                    except Exception as e:
                        result = ToolResult(success=False, error=str(e))
                else:
                    result = await self.registry.execute(name, args)

                self._emit("tool_result", {
                    "tool": name,
                    "success": result.success,
                    "output": result.output if result.success else result.error,
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result.to_message_content(),
                })

        self._emit("agent_finish", {"summary": "Max rounds reached", "max_rounds": True})
        return AgentLoopResult(
            success=False,
            summary="Max agent rounds reached",
            rounds=rounds,
            tool_calls_count=tool_calls_count,
            error="max_rounds_exceeded",
        )

    async def _execute_skill(self, skill_name: str, args: dict[str, Any]) -> Any:
        if self.skill_executor:
            import asyncio
            result = self.skill_executor(skill_name, args)
            if asyncio.iscoroutine(result):
                return await result
            return result
        return {"error": "No skill executor configured"}
