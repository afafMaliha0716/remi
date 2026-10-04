"""Progress endpoints: profile, focus sessions, and the end-of-day check-in."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from ..db import get_session
from ..models import FocusSession, Reflection, Status, Step, Task, XpEvent
from ..schemas import (
    BadgeRead,
    FocusCreate,
    Profile,
    ReflectionCreate,
    ReflectionRead,
    XpAward,
)
from ..services import gamify
from .tasks import local_day

router = APIRouter(prefix="/api", tags=["progress"])


def _sum(session: Session, column) -> int:
    return session.exec(select(func.coalesce(func.sum(column), 0))).one()


def _count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


@router.get("/profile", response_model=Profile)
def profile(session: Session = Depends(get_session)) -> Profile:
    today = date.today()
    tasks = list(session.exec(select(Task)))
    done_days = [local_day(t.completed_at) for t in tasks if t.completed_at is not None]
    streak_days = gamify.streak(set(done_days), today)
    focus_minutes = _sum(session, FocusSession.minutes)
    xp = _sum(session, XpEvent.amount)
    level = gamify.level_for(xp)

    totals = gamify.Totals(
        tasks_done=len(done_days),
        streak_days=streak_days,
        focus_minutes=focus_minutes,
        reflections=_count(session, Reflection),
        breakdowns=session.exec(select(func.count(func.distinct(Step.task_id)))).one(),
    )
    reflected = session.exec(select(Reflection).where(Reflection.day == today)).first()

    return Profile(
        xp=xp,
        level=level.level,
        level_title=level.title,
        xp_into_level=level.xp_into_level,
        xp_for_next=level.xp_for_next,
        streak_days=streak_days,
        completed_today=sum(day == today for day in done_days),
        daily_goal=gamify.DAILY_GOAL,
        open_count=sum(t.status is Status.todo for t in tasks),
        focus_minutes=focus_minutes,
        reflected_today=reflected is not None,
        badges=[BadgeRead(**vars(b)) for b in gamify.badges_for(totals)],
    )


@router.post("/focus", response_model=XpAward, status_code=201)
def record_focus(body: FocusCreate, session: Session = Depends(get_session)) -> XpAward:
    """Record a finished focus timer and award XP for the time spent."""
    awarded = gamify.focus_xp(body.minutes)
    session.add(FocusSession(task_id=body.task_id, minutes=body.minutes))
    if awarded:
        session.add(XpEvent(amount=awarded, reason="focus"))
    session.commit()
    return XpAward(xp_awarded=awarded)


@router.get("/reflections/today", response_model=ReflectionRead | None)
def todays_reflection(session: Session = Depends(get_session)) -> Reflection | None:
    return session.exec(select(Reflection).where(Reflection.day == date.today())).first()


@router.post("/reflections", response_model=ReflectionRead, status_code=201)
def save_reflection(
    body: ReflectionCreate, session: Session = Depends(get_session)
) -> ReflectionRead:
    """Save today's check-in. Doing it again the same day updates it."""
    today = date.today()
    reflection = session.exec(select(Reflection).where(Reflection.day == today)).first()
    awarded = 0
    if reflection is None:
        reflection = Reflection(day=today, friction=body.friction, note=body.note)
        awarded = gamify.REFLECTION_XP
        session.add(XpEvent(amount=awarded, reason="reflection"))
    else:
        reflection.friction = body.friction
        reflection.note = body.note
    session.add(reflection)
    session.commit()
    session.refresh(reflection)
    return ReflectionRead(
        day=reflection.day,
        friction=reflection.friction,
        note=reflection.note,
        xp_awarded=awarded,
    )
