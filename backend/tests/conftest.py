import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.services.planner import HeuristicPlanner, get_planner


@pytest.fixture
def session():
    """A fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    # Tests never call the real model.
    app.dependency_overrides[get_planner] = HeuristicPlanner
    yield TestClient(app)
    app.dependency_overrides.clear()
