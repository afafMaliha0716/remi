"""Scores tasks so Remi can answer "what should I do next?".

The score is a sum of small, explainable signals rather than a black box.
Every signal that fires adds a short reason, which the app shows next to the
task so the ordering never feels arbitrary.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ..models import Energy, Task

# A task skipped this many times is probably too big or too vague.
BREAKDOWN_SKIP_THRESHOLD = 3
QUICK_WIN_MINUTES = 10
# "Not now" pushes a task down the list for this long.
SNOOZE = timedelta(hours=2)


@dataclass
class Priority:
    score: float = 0
    reasons: list[str] = field(default_factory=list)
    suggest_breakdown: bool = False

    def add(self, points: float, reason: str | None = None) -> None:
        self.score += points
        if reason:
            self.reasons.append(reason)


def score_task(
    task: Task,
    *,
    today: date,
    now: datetime,
    energy: Energy | None = None,
    minutes_available: int | None = None,
) -> Priority:
    """Score one open task for the user's current energy and free time."""
    p = Priority()

    # Deadlines dominate: an overdue task outranks anything without one.
    if task.due_date is not None:
        days_left = (task.due_date - today).days
        if days_left < 0:
            p.add(50, "Overdue")
        elif days_left == 0:
            p.add(40, "Due today")
        elif days_left == 1:
            p.add(30, "Due tomorrow")
        elif days_left <= 3:
            p.add(20, f"Due in {days_left} days")
        elif days_left <= 7:
            p.add(10, "Due this week")

    p.add(task.importance * 10, "Marked important" if task.importance == 3 else None)

    # Small tasks build momentum, which matters more than optimal ordering.
    if task.estimated_minutes is not None and task.estimated_minutes <= QUICK_WIN_MINUTES:
        p.add(8, "Quick win")

    if energy is not None:
        if task.energy.level <= energy.level:
            p.add(10, f"Fits your {energy.value} energy")
        else:
            p.add(-15 * (task.energy.level - energy.level))

    if minutes_available is not None and task.estimated_minutes is not None:
        if task.estimated_minutes <= minutes_available:
            p.add(6, f"Fits in {minutes_available} minutes")
        else:
            p.add(-20)

    # Older tasks drift upward slowly so nothing is buried forever.
    age_days = max((now - task.created_at).days, 0)
    p.add(min(age_days, 10))

    # A task the user just said "not now" to steps aside for a while.
    if task.last_skipped_at is not None and now - task.last_skipped_at < SNOOZE:
        p.add(-100)

    if task.skip_count >= BREAKDOWN_SKIP_THRESHOLD and not task.steps:
        p.suggest_breakdown = True
        p.reasons.append(
            f"Skipped {task.skip_count} times, so try breaking it down"
        )

    return p


def rank_tasks(
    tasks: list[Task],
    *,
    today: date,
    now: datetime,
    energy: Energy | None = None,
    minutes_available: int | None = None,
) -> list[tuple[Task, Priority]]:
    """Return open tasks with their priorities, highest score first."""
    scored = [
        (
            t,
            score_task(
                t,
                today=today,
                now=now,
                energy=energy,
                minutes_available=minutes_available,
            ),
        )
        for t in tasks
    ]
    # Ties go to the task skipped least, then the oldest.
    scored.sort(key=lambda tp: (-tp[1].score, tp[0].skip_count, tp[0].created_at))
    return scored
