"""Database engine and session handling."""

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

_settings = get_settings()
_connect_args = (
    {"check_same_thread": False}
    if _settings.sqlalchemy_url.startswith("sqlite")
    else {}
)
engine = create_engine(_settings.sqlalchemy_url, connect_args=_connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
