from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app

TEST_DATABASE_URL = "postgresql+psycopg://relayops:relayops@localhost:5433/relayops_test"
test_engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(autouse=True)
def reset_test_database() -> Generator[None, None, None]:
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    with Session(test_engine) as db:
        yield db


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()