"""Terminal visualization with rich."""

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree

console = Console()


class TerminalRenderer:
    """Render agent execution flow in terminal."""

    def __init__(self):
        self.tree: Optional[Tree] = None
        self._round_nodes: dict[int, Tree] = {}

    def start(self, task: str, session_id: str) -> None:
        self.tree = Tree(f"[bold blue]Agent4Music[/] session={session_id}")
        self.tree.add(f"[green]Task:[/] {task[:100]}")
        console.print(Panel(f"Starting agent session {session_id}", title="Agent4Music"))

    def on_event(self, event_type: str, data: dict[str, Any]) -> None:
        if not self.tree:
            return

        if event_type == "round_start":
            round_num = data.get("round", 0)
            node = self.tree.add(f"[yellow]Round {round_num}[/]")
            self._round_nodes[round_num] = node

        elif event_type == "tool_call":
            round_num = data.get("round", 0)
            parent = self._round_nodes.get(round_num, self.tree)
            tool = data.get("tool", "")
            args = data.get("args", {})
            branch = parent.add(f"[cyan]Tool:[/] {tool}")
            if args:
                branch.add(Syntax(str(args)[:500], "json", theme="monokai"))

        elif event_type == "skill_call":
            skill = data.get("skill", "")
            self.tree.add(f"[magenta]Skill:[/] {skill}")

        elif event_type == "tool_result":
            tool = data.get("tool", "")
            success = data.get("success", False)
            status = "[green]OK[/]" if success else "[red]FAIL[/]"
            self.tree.add(f"{status} {tool}")

        elif event_type == "agent_finish":
            summary = data.get("summary", "")
            console.print(Panel(summary, title="Task Complete", border_style="green"))

        elif event_type == "error":
            console.print(Panel(data.get("message", ""), title="Error", border_style="red"))

    def render(self) -> None:
        if self.tree:
            console.print(self.tree)
