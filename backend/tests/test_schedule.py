from datetime import datetime

from app.models import Task
from app.services.schedule import build_plan, round_up

START = datetime(2026, 3, 4, 9, 2)


def task(id, minutes=None, title=None):
    return Task(id=id, title=title or f"Task {id}", estimated_minutes=minutes)


def times(plan):
    return [(b.kind, b.start.strftime("%H:%M"), b.end.strftime("%H:%M")) for b in plan]


def test_round_up_to_five_minutes():
    assert round_up(datetime(2026, 3, 4, 9, 2, 30)) == datetime(2026, 3, 4, 9, 5)
    assert round_up(datetime(2026, 3, 4, 9, 5)) == datetime(2026, 3, 4, 9, 5)
    assert round_up(datetime(2026, 3, 4, 9, 58)) == datetime(2026, 3, 4, 10, 0)


def test_empty_list_gives_an_empty_plan():
    assert build_plan([], START) == []


def test_tasks_are_laid_out_in_order_with_breaks_between():
    plan = build_plan([task(1, 30), task(2, 10)], START)
    assert times(plan) == [
        ("task", "09:05", "09:35"),
        ("break", "09:35", "09:40"),
        ("task", "09:40", "09:50"),
    ]
    assert [b.task_id for b in plan] == [1, None, 2]


def test_task_without_an_estimate_gets_25_minutes():
    plan = build_plan([task(1)], START)
    assert times(plan) == [("task", "09:05", "09:30")]


def test_long_break_after_ninety_minutes_of_work():
    plan = build_plan([task(1, 60), task(2, 30), task(3, 20)], START)
    breaks = [b.title for b in plan if b.kind == "break"]
    assert breaks == ["Break", "Long break"]


def test_plan_is_capped_at_six_tasks():
    plan = build_plan([task(i, 10) for i in range(1, 12)], START)
    assert sum(b.kind == "task" for b in plan) == 6


def test_task_too_long_for_the_window_is_left_out():
    plan = build_plan([task(1, 300), task(2, 20)], START)
    assert [b.task_id for b in plan if b.kind == "task"] == [2]
