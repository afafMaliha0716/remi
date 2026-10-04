"""Builds a time-blocked plan for the next few hours from ranked tasks."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models import Task

DEFAULT_MINUTES = 25
SHORT_BREAK = 5
LONG_BREAK = 15
# After this much work in a row, the next break is a long one.
LONG_BREAK_AFTER = 90
MAX_PLAN_MINUTES = 4 * 60
MAX_TASKS = 6


@dataclass
class Block:
    kind: str  # "task" or "break"
    title: str
    start: datetime
    end: datetime
    task_id: int | None = None


def round_up(moment: datetime, minutes: int = 5) -> datetime:
    """Round up to the next multiple of ``minutes`` so times are easy to read."""
    moment = moment.replace(second=0, microsecond=0)
    remainder = moment.minute % minutes
    if remainder:
        moment += timedelta(minutes=minutes - remainder)
    return moment


def build_plan(ranked_tasks: list[Task], start: datetime) -> list[Block]:
    """Lay tasks end to end with breaks between them.

    Tasks arrive already ranked, so the plan front-loads what matters most.
    It stops after a few hours: a plan for the whole day is the kind of
    thing that gets abandoned by lunch.
    """
    blocks: list[Block] = []
    cursor = round_up(start)
    plan_end = cursor + timedelta(minutes=MAX_PLAN_MINUTES)
    worked = 0
    count = 0

    for task in ranked_tasks:
        if count == MAX_TASKS:
            break
        minutes = task.estimated_minutes or DEFAULT_MINUTES
        if cursor + timedelta(minutes=minutes) > plan_end:
            continue

        if blocks:
            long_break = worked >= LONG_BREAK_AFTER
            pause = LONG_BREAK if long_break else SHORT_BREAK
            end = cursor + timedelta(minutes=pause)
            blocks.append(Block("break", "Long break" if long_break else "Break", cursor, end))
            cursor = end
            if long_break:
                worked = 0

        end = cursor + timedelta(minutes=minutes)
        blocks.append(Block("task", task.title, cursor, end, task.id))
        cursor = end
        worked += minutes
        count += 1

    return blocks
