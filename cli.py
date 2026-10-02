"""Command line interface LifeTrack."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import date

from lifetrack import __version__
from lifetrack.config import Settings
from lifetrack.exceptions import AppError
from lifetrack.logging_config import setup_logging
from lifetrack.services import GoalService, HabitService, JournalService, build_summary
from lifetrack.store import JsonStore

logger = logging.getLogger(__name__)


def _stars(mood: int) -> str:
    return "★" * mood + "☆" * (5 - mood)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lifetrack", description="Pelacak kehidupan: jurnal, kebiasaan, dan target."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    groups = parser.add_subparsers(dest="group", required=True)

    journal = groups.add_parser("journal", help="Jurnal harian dengan mood")
    j = journal.add_subparsers(dest="action", required=True)
    ja = j.add_parser("add", help="Tulis jurnal")
    ja.add_argument("text")
    ja.add_argument("--mood", type=int, default=3, help="1 sampai 5")
    jl = j.add_parser("list", help="Lihat jurnal terbaru")
    jl.add_argument("--limit", type=int, default=10)

    habit = groups.add_parser("habit", help="Pelacak kebiasaan")
    h = habit.add_subparsers(dest="action", required=True)
    ha = h.add_parser("add", help="Tambah kebiasaan")
    ha.add_argument("name")
    hc = h.add_parser("check", help="Centang kebiasaan hari ini")
    hc.add_argument("name")
    hc.add_argument("--date", type=date.fromisoformat, help="YYYY-MM-DD (opsional)")
    h.add_parser("list", help="Daftar kebiasaan dan streak")

    goal = groups.add_parser("goal", help="Target hidup")
    g = goal.add_subparsers(dest="action", required=True)
    ga = g.add_parser("add", help="Tambah target")
    ga.add_argument("title")
    ga.add_argument("--target", type=int, required=True)
    ga.add_argument("--unit", default="")
    gp = g.add_parser("progress", help="Tambah progres target")
    gp.add_argument("goal_id", type=int)
    gp.add_argument("amount", type=int)
    g.add_parser("list", help="Daftar target")

    groups.add_parser("summary", help="Ringkasan 7 hari terakhir")
    return parser


def _run(args: argparse.Namespace, store: JsonStore) -> None:
    if args.group == "journal":
        svc = JournalService(store)
        if args.action == "add":
            e = svc.add(args.text, args.mood)
            print(f"Jurnal tersimpan ({e.date}) {_stars(e.mood)}")
        else:
            entries = svc.list_all(args.limit)
            if not entries:
                print("Belum ada jurnal.")
            for e in entries:
                print(f"{e.date} | {_stars(e.mood)} | {e.text}")

    elif args.group == "habit":
        hsvc = HabitService(store)
        if args.action == "add":
            print(f"Kebiasaan ditambahkan: {hsvc.add(args.name).name}")
        elif args.action == "check":
            habit = hsvc.check(args.name, args.date)
            print(f"Tercentang: {habit.name} (total {len(habit.checkins)} hari)")
        else:
            habits = hsvc.list_all()
            if not habits:
                print("Belum ada kebiasaan.")
            for hb in habits:
                streak = HabitService.compute_streak(hb.checkins, date.today())
                print(f"{hb.name}: streak {streak} hari, total {len(hb.checkins)} hari")

    elif args.group == "goal":
        gsvc = GoalService(store)
        if args.action == "add":
            goal = gsvc.add(args.title, args.target, args.unit)
            print(f"Target dibuat: #{goal.id} {goal.title}")
        elif args.action == "progress":
            goal = gsvc.add_progress(args.goal_id, args.amount)
            print(f"#{goal.id} {goal.title}: {goal.progress}/{goal.target} ({goal.percent}%)")
        else:
            goals = gsvc.list_all()
            if not goals:
                print("Belum ada target.")
            for goal in goals:
                print(
                    f"#{goal.id} {goal.title}: {goal.progress}/{goal.target} "
                    f"{goal.unit} ({goal.percent}%)".replace("  ", " ")
                )

    else:  # summary
        s = build_summary(store)
        print(f"Ringkasan {s.start} s/d {s.end}")
        mood = f"{s.avg_mood}/5" if s.avg_mood is not None else "-"
        print(f"- Jurnal: {s.entries} entri, rata-rata mood {mood}")
        for st in s.habits:
            print(f"- Kebiasaan {st.name}: {st.done_days}/7 hari, streak {st.streak}")
        for goal in s.goals:
            print(f"- Target {goal.title}: {goal.percent}%")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    setup_logging(settings.log_level)
    try:
        _run(args, JsonStore(settings.data_file))
    except AppError as exc:
        logger.error("%s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
