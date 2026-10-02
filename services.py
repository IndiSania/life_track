"""Logika bisnis LifeTrack."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta

from lifetrack.exceptions import NotFoundError, ValidationError
from lifetrack.models import Goal, Habit, JournalEntry
from lifetrack.store import JsonStore

Clock = Callable[[], date]


def _next_id(items: list[dict[str, object]]) -> int:
    return max((int(str(i["id"])) for i in items), default=0) + 1


class JournalService:
    def __init__(self, store: JsonStore, clock: Clock = date.today) -> None:
        self._store = store
        self._clock = clock

    def add(self, text: str, mood: int = 3) -> JournalEntry:
        text = text.strip()
        if not text:
            raise ValidationError("Isi jurnal tidak boleh kosong.")
        if not 1 <= mood <= 5:
            raise ValidationError("Mood harus antara 1 sampai 5.")
        state = self._store.load()
        entry = JournalEntry(
            id=_next_id(state["journal"]), date=self._clock().isoformat(), text=text, mood=mood
        )
        state["journal"].append(entry.to_dict())
        self._store.save(state)
        return entry

    def list_all(self, limit: int | None = None) -> list[JournalEntry]:
        entries = [JournalEntry.from_dict(d) for d in self._store.load()["journal"]]
        entries.sort(key=lambda e: (e.date, e.id), reverse=True)
        return entries[:limit] if limit else entries


class HabitService:
    def __init__(self, store: JsonStore, clock: Clock = date.today) -> None:
        self._store = store
        self._clock = clock

    def add(self, name: str) -> Habit:
        name = name.strip()
        if not name:
            raise ValidationError("Nama kebiasaan tidak boleh kosong.")
        state = self._store.load()
        if any(h["name"].lower() == name.lower() for h in state["habits"]):
            raise ValidationError(f"Kebiasaan '{name}' sudah ada.")
        habit = Habit(id=_next_id(state["habits"]), name=name)
        state["habits"].append(habit.to_dict())
        self._store.save(state)
        return habit

    def check(self, name: str, day: date | None = None) -> Habit:
        state = self._store.load()
        for raw in state["habits"]:
            if raw["name"].lower() == name.strip().lower():
                habit = Habit.from_dict(raw)
                iso = (day or self._clock()).isoformat()
                if iso not in habit.checkins:
                    habit.checkins.append(iso)
                    habit.checkins.sort()
                raw.update(habit.to_dict())
                self._store.save(state)
                return habit
        raise NotFoundError(f"Kebiasaan '{name}' tidak ditemukan.")

    def list_all(self) -> list[Habit]:
        return [Habit.from_dict(d) for d in self._store.load()["habits"]]

    @staticmethod
    def compute_streak(checkins: list[str], today: date) -> int:
        """Hitung hari berturut-turut. Streak tetap hidup jika hari ini belum dicek
        tetapi kemarin sudah."""
        days = {date.fromisoformat(c) for c in checkins}
        cursor = today if today in days else today - timedelta(days=1)
        streak = 0
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak


class GoalService:
    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def add(self, title: str, target: int, unit: str = "") -> Goal:
        title = title.strip()
        if not title:
            raise ValidationError("Judul target tidak boleh kosong.")
        if target <= 0:
            raise ValidationError("Target harus lebih dari 0.")
        state = self._store.load()
        goal = Goal(id=_next_id(state["goals"]), title=title, target=target, unit=unit)
        state["goals"].append(goal.to_dict())
        self._store.save(state)
        return goal

    def add_progress(self, goal_id: int, amount: int) -> Goal:
        if amount <= 0:
            raise ValidationError("Jumlah progres harus lebih dari 0.")
        state = self._store.load()
        for raw in state["goals"]:
            if raw["id"] == goal_id:
                goal = Goal.from_dict(raw)
                goal.progress = min(goal.target, goal.progress + amount)
                raw.update(goal.to_dict())
                self._store.save(state)
                return goal
        raise NotFoundError(f"Target #{goal_id} tidak ditemukan.")

    def list_all(self) -> list[Goal]:
        return [Goal.from_dict(d) for d in self._store.load()["goals"]]


@dataclass
class HabitStat:
    name: str
    done_days: int
    streak: int


@dataclass
class Summary:
    start: date
    end: date
    entries: int
    avg_mood: float | None
    habits: list[HabitStat]
    goals: list[Goal]


def build_summary(store: JsonStore, clock: Clock = date.today, days: int = 7) -> Summary:
    end = clock()
    start = end - timedelta(days=days - 1)
    journal = JournalService(store, clock).list_all()
    in_range = [e for e in journal if start <= date.fromisoformat(e.date) <= end]
    avg = round(sum(e.mood for e in in_range) / len(in_range), 1) if in_range else None

    habit_stats = []
    for h in HabitService(store, clock).list_all():
        done = sum(1 for c in h.checkins if start <= date.fromisoformat(c) <= end)
        habit_stats.append(HabitStat(h.name, done, HabitService.compute_streak(h.checkins, end)))

    return Summary(start, end, len(in_range), avg, habit_stats, GoalService(store).list_all())
