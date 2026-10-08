from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from auth_service.config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}

engine = create_engine(_settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables that do not yet exist."""
    from auth_service.infrastructure.persistence import models  # noqa: F401  (registers mappings)

    Base.metadata.create_all(bind=engine)
