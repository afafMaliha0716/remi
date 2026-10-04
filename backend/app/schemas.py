"""Request and response shapes for the API."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from .models import Energy, Status


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


class BrainDumpRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class BrainDumpResponse(BaseModel):
    planner: str
    tasks: list[TaskRead]


class Stats(BaseModel):
    open_count: int
    completed_today: int
    streak_days: int
