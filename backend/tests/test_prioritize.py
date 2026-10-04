from datetime import date, datetime, timedelta, timezone

from app.models import Energy, Step, Task
from app.services.prioritize import rank_tasks, score_task

TODAY = date(2026, 3, 4)
NOW = datetime(2026, 3, 4, 12, 0, tzinfo=timezone.utc)


def make(title="Task", **kwargs) -> Task:
    kwargs.setdefault("created_at", NOW)
    return Task(title=title, **kwargs)


def score(task, **kwargs):
    return score_task(task, today=TODAY, now=NOW, **kwargs)


def order(tasks, **kwargs):
    ranked = rank_tasks(tasks, today=TODAY, now=NOW, **kwargs)
    return [t.title for t, _ in ranked]


def test_overdue_beats_due_today_beats_no_deadline():
    tasks = [
        make("none"),
        make("today", due_date=TODAY),
        make("overdue", due_date=TODAY - timedelta(days=2)),
    ]
    assert order(tasks) == ["overdue", "today", "none"]


def test_due_reasons_are_explained():
    assert "Overdue" in score(make(due_date=TODAY - timedelta(days=1))).reasons
    assert "Due today" in score(make(due_date=TODAY)).reasons
    assert "Due tomorrow" in score(make(due_date=TODAY + timedelta(days=1))).reasons
    assert score(make(due_date=TODAY + timedelta(days=30))).reasons == []


def test_importance_raises_score():
    assert score(make(importance=3)).score > score(make(importance=1)).score
    assert "Marked important" in score(make(importance=3)).reasons


def test_quick_win_gets_a_boost():
    quick = score(make(estimated_minutes=5))
    long = score(make(estimated_minutes=60))
    assert quick.score > long.score
    assert "Quick win" in quick.reasons


def test_low_energy_prefers_low_energy_tasks():
    tasks = [make("deep", energy=Energy.high), make("easy", energy=Energy.low)]
    assert order(tasks, energy=Energy.low) == ["easy", "deep"]


def test_high_energy_does_not_penalize_any_task():
    for level in Energy:
        p = score(make(energy=level), energy=Energy.high)
        assert "Fits your high energy" in p.reasons


def test_task_that_does_not_fit_the_time_drops():
    tasks = [make("long", estimated_minutes=90), make("short", estimated_minutes=15)]
    assert order(tasks, minutes_available=20) == ["short", "long"]


def test_urgent_deadline_still_wins_at_low_energy():
    tasks = [
        make("easy", energy=Energy.low),
        make("essay", energy=Energy.high, due_date=TODAY - timedelta(days=1)),
    ]
    assert order(tasks, energy=Energy.low)[0] == "essay"


def test_older_tasks_drift_upward_with_a_cap():
    fresh = score(make())
    week_old = score(make(created_at=NOW - timedelta(days=7)))
    ancient = score(make(created_at=NOW - timedelta(days=400)))
    assert week_old.score == fresh.score + 7
    assert ancient.score == fresh.score + 10


def test_repeated_skips_suggest_a_breakdown():
    assert not score(make(skip_count=2)).suggest_breakdown
    assert score(make(skip_count=3)).suggest_breakdown


def test_no_breakdown_suggestion_once_steps_exist():
    task = make(skip_count=5)
    task.steps = [Step(title="first step", task_id=1)]
    assert not score(task).suggest_breakdown


def test_ties_go_to_the_task_skipped_least():
    tasks = [make("skipped", skip_count=2), make("fresh")]
    assert order(tasks) == ["fresh", "skipped"]


def test_just_skipped_task_steps_aside_then_returns():
    urgent = make("urgent", due_date=TODAY, last_skipped_at=NOW - timedelta(minutes=5))
    other = make("other")
    assert order([urgent, other]) == ["other", "urgent"]

    urgent.last_skipped_at = NOW - timedelta(hours=3)
    assert order([urgent, other]) == ["urgent", "other"]
