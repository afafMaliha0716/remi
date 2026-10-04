from datetime import date, timedelta

from app.models import Energy
from app.services.gamify import (
    TASK_XP,
    Totals,
    badges_for,
    focus_xp,
    level_for,
    streak,
    xp_to_reach,
)

TODAY = date(2026, 3, 4)


def days_ago(*offsets):
    return {TODAY - timedelta(days=n) for n in offsets}


def test_harder_tasks_earn_more_xp():
    assert TASK_XP[Energy.low] < TASK_XP[Energy.medium] < TASK_XP[Energy.high]


def test_focus_xp_counts_full_five_minute_blocks_and_is_capped():
    assert focus_xp(4) == 0
    assert focus_xp(5) == 5
    assert focus_xp(25) == 25
    assert focus_xp(500) == 60


def test_level_thresholds_grow():
    assert [xp_to_reach(n) for n in (1, 2, 3, 4)] == [0, 100, 300, 600]


def test_level_for_reports_progress_within_the_level():
    start = level_for(0)
    assert (start.level, start.title, start.xp_into_level, start.xp_for_next) == (
        1,
        "Sand Grain",
        0,
        100,
    )
    assert level_for(99).level == 1
    mid = level_for(150)
    assert (mid.level, mid.xp_into_level, mid.xp_for_next) == (2, 50, 200)


def test_level_title_stops_at_the_last_one():
    assert level_for(1_000_000).title == "Nautilus"


def test_streak_counts_consecutive_days():
    assert streak(set(), TODAY) == 0
    assert streak(days_ago(0), TODAY) == 1
    assert streak(days_ago(0, 1, 2), TODAY) == 3
    assert streak(days_ago(0, 2, 3), TODAY) == 1


def test_streak_stays_alive_until_today_is_over():
    assert streak(days_ago(1, 2), TODAY) == 2
    assert streak(days_ago(2, 3), TODAY) == 0


def earned(**totals):
    return {b.id for b in badges_for(Totals(**totals)) if b.earned}


def test_badges_unlock_from_totals():
    assert earned() == set()
    assert earned(tasks_done=1) == {"first_wave"}
    assert earned(streak_days=7) == {"high_tide", "full_moon"}
    assert "deep_dive" in earned(focus_minutes=60)
    assert "small_steps" in earned(breakdowns=1)
    assert "looking_back" in earned(reflections=3)
    assert "treasure" in earned(tasks_done=25)
