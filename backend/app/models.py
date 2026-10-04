"""Database tables."""

from datetime import date, datetime, timezone
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Energy(str, Enum):
    """How much focus a task takes, or how much the user has right now."""

    low = "low"
    medium = "medium"
    high = "high"

    @property
    def level(self) -> int:
        return {"low": 1, "medium": 2, "high": 3}[self.value]


class Status(str, Enum):
    todo = "todo"
    done = "done"


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    notes: str = ""
    status: Status = Field(default=Status.todo, index=True)
    energy: Energy = Energy.medium
    importance: int = Field(default=2, ge=1, le=3)
    estimated_minutes: int | None = Field(default=None, ge=1)
    due_date: date | None = None
    skip_count: int = 0
    last_skipped_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    steps: list["Step"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Step.position",
        },
    )


class Step(SQLModel, table=True):
    """One small, concrete action inside a task."""

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id", index=True)
    title: str = Field(max_length=200)
    done: bool = False
    position: int = 0

    task: Task | None = Relationship(back_populates="steps")


class XpEvent(SQLModel, table=True):
    """One award of experience points. A user's XP is the sum of these."""

    id: int | None = Field(default=None, primary_key=True)
    amount: int
    reason: str
    task_id: int | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utcnow)


class FocusSession(SQLModel, table=True):
    """A finished focus timer."""

    id: int | None = Field(default=None, primary_key=True)
    task_id: int | None = None
    minutes: int = Field(ge=1)
    created_at: datetime = Field(default_factory=utcnow)


class Reflection(SQLModel, table=True):
    """The end-of-day check-in. One per day."""

    id: int | None = Field(default=None, primary_key=True)
    day: date = Field(index=True, unique=True)
    # How hard it was to get started today: 1 (easy) to 5 (very hard).
    friction: int = Field(ge=1, le=5)
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class ChatRole(str, Enum):
    user = "user"
    remi = "remi"


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: ChatRole
    content: str
    created_at: datetime = Field(default_factory=utcnow)
