"""Shared API enums and schemas."""

from __future__ import annotations

from enum import Enum


class MusicSource(str, Enum):
    qq = "qq"
    netease = "netease"

    @classmethod
    def labels(cls) -> dict[str, str]:
        return {"qq": "QQ音乐", "netease": "网易云音乐"}


class ChartType(str, Enum):
    hot = "hot"
    new = "new"
    surge = "surge"
    original = "original"
    pop = "pop"
    electronic = "electronic"
