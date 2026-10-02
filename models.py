"""Model domain: jurnal, kebiasaan, dan target hidup."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class JournalEntry:
    id: int
    date: str  # format ISO: YYYY-MM-DD
    text: str
    mood: int  # 1 (buruk) sampai 5 (sangat baik)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JournalEntry:
        return cls(**data)


@dataclass
class Habit:
    id: int
    name: str
    checkins: list[str] = field(default_factory=list)  # daftar tanggal ISO

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Habit:
        return cls(**data)


@dataclass
class Goal:
    id: int
    title: str
    target: int
    unit: str = ""
    progress: int = 0

    @property
    def percent(self) -> int:
        return min(100, round(self.progress * 100 / self.target))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Goal:
        return cls(**data)
