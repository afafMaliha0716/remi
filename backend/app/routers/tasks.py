"""Task endpoints: CRUD, completion, skipping, breakdown, and "what next"."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, select

from ..db import get_session
from ..models import Energy, Status, Step, Task, XpEvent, utcnow
from ..schemas import (
    BrainDumpRequest,
    BrainDumpResponse,
    Stats,
    StepRead,
    StepUpdate,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from ..services.gamify import TASK_XP, streak
from ..services.planner import Planner, get_planner
from ..services.prioritize import Priority, rank_tasks, score_task

router = APIRouter(prefix="/api", tags=["tasks"])


def _to_read(task: Task, priority: Priority | None = None) -> TaskRead:
    read = TaskRead.model_validate(task, from_attributes=True)
    if priority is not None:
        read.score = priority.score
        read.reasons = priority.reasons
        read.suggest_breakdown = priority.suggest_breakdown
    return read


def _scored(task: Task) -> TaskRead:
    if task.status is Status.done:
        return _to_read(task)
    return _to_read(task, score_task(task, today=date.today(), now=utcnow()))


def _get_task(task_id: int, session: Session) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


def _save(task: Task, session: Session) -> Task:
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.post("/brain-dump", response_model=BrainDumpResponse, status_code=201)
def brain_dump(
    body: BrainDumpRequest,
    session: Session = Depends(get_session),
    planner: Planner = Depends(get_planner),
) -> BrainDumpResponse:
    """Turn free-form text into saved, structured tasks."""
    planned = planner.parse_brain_dump(body.text, date.today())
    tasks = [
        Task(
            title=p.title,
            energy=p.energy,
            importance=p.importance,
            estimated_minutes=p.estimated_minutes,
            due_date=p.due_date,
        )
        for p in planned
    ]
    session.add_all(tasks)
    session.commit()
    for task in tasks:
        session.refresh(task)
    return BrainDumpResponse(planner=planner.name, tasks=[_scored(t) for t in tasks])


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    status_filter: Status = Query(Status.todo, alias="status"),
    energy: Energy | None = None,
    minutes: int | None = Query(None, ge=1),
    session: Session = Depends(get_session),
) -> list[TaskRead]:
    """Open tasks ranked by priority, or completed tasks newest first."""
    tasks = list(session.exec(select(Task).where(Task.status == status_filter)))
    if status_filter is Status.done:
        tasks.sort(key=lambda t: t.completed_at or t.created_at, reverse=True)
        return [_to_read(t) for t in tasks]
    ranked = rank_tasks(
        tasks,
        today=date.today(),
        now=utcnow(),
        energy=energy,
        minutes_available=minutes,
    )
    return [_to_read(task, priority) for task, priority in ranked]


@router.get("/tasks/next", response_model=TaskRead | None)
def next_task(
    energy: Energy | None = None,
    minutes: int | None = Query(None, ge=1),
    session: Session = Depends(get_session),
) -> TaskRead | None:
    """The single best task to do right now, or null when the list is clear."""
    tasks = list(session.exec(select(Task).where(Task.status == Status.todo)))
    ranked = rank_tasks(
        tasks,
        today=date.today(),
        now=utcnow(),
        energy=energy,
        minutes_available=minutes,
    )
    if not ranked:
        return None
    task, priority = ranked[0]
    return _to_read(task, priority)


@router.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(body: TaskCreate, session: Session = Depends(get_session)) -> TaskRead:
    return _scored(_save(Task(**body.model_dump()), session))


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int, body: TaskUpdate, session: Session = Depends(get_session)
) -> TaskRead:
    task = _get_task(task_id, session)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    return _scored(_save(task, session))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)) -> Response:
    session.delete(_get_task(task_id, session))
    session.commit()
    return Response(status_code=204)


@router.post("/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(task_id: int, session: Session = Depends(get_session)) -> TaskRead:
    task = _get_task(task_id, session)
    awarded = 0
    if task.status is not Status.done:
        task.status = Status.done
        task.completed_at = utcnow()
        awarded = TASK_XP[task.energy]
        session.add(XpEvent(amount=awarded, reason="task", task_id=task.id))
    for step in task.steps:
        step.done = True
    read = _scored(_save(task, session))
    read.xp_awarded = awarded
    return read


@router.post("/tasks/{task_id}/reopen", response_model=TaskRead)
def reopen_task(task_id: int, session: Session = Depends(get_session)) -> TaskRead:
    task = _get_task(task_id, session)
    task.status = Status.todo
    task.completed_at = None
    # Take back the XP so finishing the same task twice can't be farmed.
    for event in session.exec(select(XpEvent).where(XpEvent.task_id == task.id)):
        session.delete(event)
    return _scored(_save(task, session))


@router.post("/tasks/{task_id}/skip", response_model=TaskRead)
def skip_task(task_id: int, session: Session = Depends(get_session)) -> TaskRead:
    """Record "not now": the task steps aside for a couple of hours.

    Repeated skips make Remi suggest a breakdown.
    """
    task = _get_task(task_id, session)
    task.skip_count += 1
    task.last_skipped_at = utcnow()
    return _scored(_save(task, session))


@router.post("/tasks/{task_id}/breakdown", response_model=TaskRead)
def break_down_task(
    task_id: int,
    session: Session = Depends(get_session),
    planner: Planner = Depends(get_planner),
) -> TaskRead:
    """Replace the task's steps with a fresh set of small, concrete ones."""
    task = _get_task(task_id, session)
    titles = planner.break_down(task.title, task.notes)
    task.steps = [Step(title=t, position=i) for i, t in enumerate(titles)]
    return _scored(_save(task, session))


@router.patch("/steps/{step_id}", response_model=StepRead)
def update_step(
    step_id: int, body: StepUpdate, session: Session = Depends(get_session)
) -> Step:
    step = session.get(Step, step_id)
    if step is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Step not found")
    step.done = body.done
    session.add(step)
    session.commit()
    session.refresh(step)
    return step


@router.get("/stats", response_model=Stats)
def stats(session: Session = Depends(get_session)) -> Stats:
    today = date.today()
    tasks = list(session.exec(select(Task)))
    completed_days = {
        local_day(t.completed_at) for t in tasks if t.completed_at is not None
    }
    return Stats(
        open_count=sum(t.status is Status.todo for t in tasks),
        completed_today=sum(
            t.completed_at is not None and local_day(t.completed_at) == today
            for t in tasks
        ),
        streak_days=streak(completed_days, today),
    )


def local_day(moment: datetime) -> date:
    """Convert a stored UTC timestamp to the server's local calendar day."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone().date()
