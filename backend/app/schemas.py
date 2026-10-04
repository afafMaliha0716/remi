"""Request and response shapes for the API."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from .models import ChatRole, Energy, Status


class StepRead(BaseModel):
    id: int
    title: str
    done: bool
    position: int


class StepUpdate(BaseModel):
    done: bool


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = ""
    energy: Energy = Energy.medium
    importance: int = Field(default=2, ge=1, le=3)
    estimated_minutes: int | None = Field(default=None, ge=1)
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    energy: Energy | None = None
    importance: int | None = Field(default=None, ge=1, le=3)
    estimated_minutes: int | None = Field(default=None, ge=1)
    due_date: date | None = None


class TaskRead(BaseModel):
    id: int
    title: str
    notes: str
    status: Status
    energy: Energy
    importance: int
    estimated_minutes: int | None
    due_date: date | None
    skip_count: int
    created_at: datetime
    completed_at: datetime | None
    steps: list[StepRead] = []
    # Filled in by the prioritizer.
    score: float = 0
    reasons: list[str] = []
    suggest_breakdown: bool = False
    # XP earned by the action that produced this response, for the app to celebrate.
    xp_awarded: int = 0


class BrainDumpRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class BrainDumpResponse(BaseModel):
    planner: str
    tasks: list[TaskRead]


class Stats(BaseModel):
    open_count: int
    completed_today: int
    streak_days: int


class BadgeRead(BaseModel):
    id: str
    name: str
    description: str
    earned: bool


class Profile(BaseModel):
    xp: int
    level: int
    level_title: str
    xp_into_level: int
    xp_for_next: int
    streak_days: int
    completed_today: int
    daily_goal: int
    open_count: int
    focus_minutes: int
    reflected_today: bool
    badges: list[BadgeRead]


class FocusCreate(BaseModel):
    minutes: int = Field(ge=1, le=240)
    task_id: int | None = None


class XpAward(BaseModel):
    xp_awarded: int


class ReflectionCreate(BaseModel):
    friction: int = Field(ge=1, le=5)
    note: str = Field(default="", max_length=1000)


class ReflectionRead(BaseModel):
    day: date
    friction: int
    note: str
    xp_awarded: int = 0


class PlanBlock(BaseModel):
    kind: str
    title: str
    start: datetime
    end: datetime
    task_id: int | None = None


class ChatMessageRead(BaseModel):
    id: int
    role: ChatRole
    content: str
    created_at: datetime


class CoachRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    mode: str | None = None
    # The user's local time, so a plan starts from their clock, not the server's.
    local_time: datetime | None = None


class CoachResponse(BaseModel):
    coach: str
    mode: str
    reply: ChatMessageRead
    suggested_task_id: int | None = None
    plan: list[PlanBlock] = []
