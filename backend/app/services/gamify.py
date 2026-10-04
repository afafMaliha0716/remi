"""XP, levels, streaks, and badges.

The rules are deliberately small and predictable: finishing things earns XP,
harder things earn more, and nothing is ever taken away for a bad day.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from ..models import Energy

DAILY_GOAL = 3

TASK_XP = {Energy.low: 10, Energy.medium: 20, Energy.high: 30}
REFLECTION_XP = 15
FOCUS_XP_PER_5_MIN = 5
FOCUS_XP_CAP = 60

# Remi is a shell, so levels are named after bigger and bigger ones.
LEVEL_TITLES = [
    "Sand Grain",
    "Periwinkle",
    "Cockle",
    "Scallop",
    "Whelk",
    "Conch",
    "Nautilus",
]


def focus_xp(minutes: int) -> int:
    return min((minutes // 5) * FOCUS_XP_PER_5_MIN, FOCUS_XP_CAP)


def xp_to_reach(level: int) -> int:
    """Total XP needed to reach a level: 0, 100, 300, 600, 1000, ..."""
    return 50 * level * (level - 1)


@dataclass
class Level:
    level: int
    title: str
    xp_into_level: int
    xp_for_next: int


def level_for(xp: int) -> Level:
    level = 1
    while xp >= xp_to_reach(level + 1):
        level += 1
    floor = xp_to_reach(level)
    return Level(
        level=level,
        title=LEVEL_TITLES[min(level, len(LEVEL_TITLES)) - 1],
        xp_into_level=xp - floor,
        xp_for_next=xp_to_reach(level + 1) - floor,
    )


def streak(completed_days: set[date], today: date) -> int:
    """Consecutive days with a completion, ending today or yesterday.

    Counting from yesterday keeps the streak alive until the day is over.
    """
    day = today if today in completed_days else today - timedelta(days=1)
    count = 0
    while day in completed_days:
        count += 1
        day -= timedelta(days=1)
    return count


@dataclass
class Totals:
    tasks_done: int = 0
    streak_days: int = 0
    focus_minutes: int = 0
    reflections: int = 0
    breakdowns: int = 0


@dataclass
class Badge:
    id: str
    name: str
    description: str
    earned: bool


_BADGES = [
    ("first_wave", "First Wave", "Finish your first task", lambda t: t.tasks_done >= 1),
    ("small_steps", "Small Steps", "Break a task into steps", lambda t: t.breakdowns >= 1),
    ("deep_dive", "Deep Dive", "Focus for 60 minutes in total", lambda t: t.focus_minutes >= 60),
    ("high_tide", "High Tide", "Keep a 3-day streak", lambda t: t.streak_days >= 3),
    ("looking_back", "Looking Back", "Do 3 end-of-day check-ins", lambda t: t.reflections >= 3),
    ("full_moon", "Full Moon", "Keep a 7-day streak", lambda t: t.streak_days >= 7),
    ("treasure", "Treasure Chest", "Finish 25 tasks", lambda t: t.tasks_done >= 25),
]


def badges_for(totals: Totals) -> list[Badge]:
    return [Badge(id, name, desc, rule(totals)) for id, name, desc, rule in _BADGES]
