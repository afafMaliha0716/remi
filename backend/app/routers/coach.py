"""Coach endpoints: the chat with Remi and the day plan."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session, select

from ..db import get_session
from ..models import ChatMessage, ChatRole, Status, Task, utcnow
from ..schemas import ChatMessageRead, CoachRequest, CoachResponse, PlanBlock
from ..services.coach import Coach, Context, Mode, detect_mode, get_coach
from ..services.prioritize import rank_tasks
from ..services.schedule import Block, build_plan

router = APIRouter(prefix="/api", tags=["coach"])

HISTORY_LIMIT = 100


def _ranked_open_tasks(session: Session) -> list[Task]:
    tasks = list(session.exec(select(Task).where(Task.status == Status.todo)))
    return [t for t, _ in rank_tasks(tasks, today=date.today(), now=utcnow())]


def _blocks(plan: list[Block]) -> list[PlanBlock]:
    return [PlanBlock(**vars(b)) for b in plan]


@router.get("/plan", response_model=list[PlanBlock])
def plan(
    start: datetime | None = Query(
        None, description="The user's local time. Defaults to the server's."
    ),
    session: Session = Depends(get_session),
) -> list[PlanBlock]:
    """A time-blocked plan for the next few hours."""
    return _blocks(build_plan(_ranked_open_tasks(session), start or datetime.now()))


@router.get("/coach/messages", response_model=list[ChatMessageRead])
def messages(session: Session = Depends(get_session)) -> list[ChatMessage]:
    recent = session.exec(
        select(ChatMessage).order_by(ChatMessage.id.desc()).limit(HISTORY_LIMIT)
    )
    return list(reversed(list(recent)))


@router.delete("/coach/messages", status_code=204)
def clear_messages(session: Session = Depends(get_session)) -> Response:
    for message in session.exec(select(ChatMessage)):
        session.delete(message)
    session.commit()
    return Response(status_code=204)


@router.post("/coach", response_model=CoachResponse)
def talk_to_coach(
    body: CoachRequest,
    session: Session = Depends(get_session),
    coach: Coach = Depends(get_coach),
) -> CoachResponse:
    """Send Remi a message and get a reply."""
    try:
        mode = Mode(body.mode) if body.mode else detect_mode(body.message)
    except ValueError:
        mode = detect_mode(body.message)

    open_tasks = _ranked_open_tasks(session)
    day_plan = (
        build_plan(open_tasks, body.local_time or datetime.now())
        if mode is Mode.plan_day
        else []
    )
    history = [
        (m.role.value, m.content)
        for m in session.exec(select(ChatMessage).order_by(ChatMessage.id.desc()).limit(8))
    ][::-1]

    reply = coach.reply(
        mode, body.message, Context(open_tasks=open_tasks, plan=day_plan, history=history)
    )

    session.add(ChatMessage(role=ChatRole.user, content=body.message))
    saved = ChatMessage(role=ChatRole.remi, content=reply.text)
    session.add(saved)
    session.commit()
    session.refresh(saved)

    return CoachResponse(
        coach=coach.name,
        mode=mode.value,
        reply=ChatMessageRead.model_validate(saved, from_attributes=True),
        suggested_task_id=reply.suggested_task_id,
        plan=_blocks(day_plan),
    )
