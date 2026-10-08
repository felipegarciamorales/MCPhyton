import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth_service.infrastructure.persistence import models  # noqa: F401  (registers table mappings)
from auth_service.infrastructure.persistence.database import Base
from auth_service.main import app
from auth_service.presentation.dependencies import get_session


@pytest.fixture
def client():
    # StaticPool keeps a single connection alive so every session shares the
    # same in-memory SQLite database instead of each getting its own empty one.
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    def _override_get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
