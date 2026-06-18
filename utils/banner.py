"""Print Agent4Music ASCII banner for CLI entrypoints."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BANNER_FILE = PROJECT_ROOT / "assets" / "banner.txt"

TAGLINE = "Agent4Music | Crawl · Analyze · Visualize"


def get_banner_text() -> str:
    if BANNER_FILE.exists():
        return BANNER_FILE.read_text(encoding="utf-8").rstrip()
    return "Agent4Music — Intelligent Music Data Agent"


def print_banner(tagline: bool = True) -> None:
    print(get_banner_text())
    if tagline:
        print()
        print(f"  {TAGLINE}")
        print()
