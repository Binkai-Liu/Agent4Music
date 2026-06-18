"""Parse SKILL.md skill documents."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"


def scan_skills(skills_dir: Optional[Path] = None) -> list[dict[str, str]]:
    """Scan skills directory and return name + short description."""
    base = skills_dir or SKILLS_DIR
    skills: list[dict[str, str]] = []

    if not base.exists():
        return skills

    for skill_dir in sorted(base.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        content = skill_md.read_text(encoding="utf-8")
        name = skill_dir.name
        description = _extract_description(content)
        skills.append({"name": name, "description": description, "path": skill_md.name})

    return skills


def load_skill_content(skill_name: str, skills_dir: Optional[Path] = None) -> Optional[str]:
    """Load full SKILL.md content for on-demand injection."""
    base = skills_dir or SKILLS_DIR
    skill_md = base / skill_name / "SKILL.md"
    if skill_md.exists():
        return skill_md.read_text(encoding="utf-8")
    return None


def _extract_description(content: str) -> str:
    """Extract first meaningful line after title as description."""
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            continue
        if line.startswith("作用：") or line.startswith("作用:"):
            return line.split("：", 1)[-1].split(":", 1)[-1].strip()
        if line and not line.startswith("##"):
            return line[:80]
    return "No description"
