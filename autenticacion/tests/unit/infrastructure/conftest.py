import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth_service.infrastructure.persistence import models  # noqa: F401  (registers table mappings)
from auth_service.infrastructure.persistence.database import Base


@pytest.fixture
def db_session():
    # StaticPool keeps a single connection alive so every session shares the
    # same in-memory SQLite database instead of each getting its own empty one.
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
