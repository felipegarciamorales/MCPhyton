from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from auth_service.domain.entities.user import ActorType, User
from auth_service.domain.repositories.user_repository import UserRepository
from auth_service.domain.value_objects.email import Email
from auth_service.infrastructure.persistence.models import UserModel
from auth_service.shared.clock import ensure_utc


class SqliteUserRepository(UserRepository):
    """SQLAlchemy-backed implementation of the UserRepository port."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> User:
        model = UserModel(
            email=str(user.email),
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            is_admin=user.is_admin,
            actor_type=user.actor_type.value,
            created_at=user.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    def get_by_email(self, email: Email) -> Optional[User]:
        statement = select(UserModel).where(UserModel.email == str(email))
        model = self._session.scalars(statement).first()
        return self._to_entity(model) if model else None

    def exists_by_email(self, email: Email) -> bool:
        statement = select(UserModel.id).where(UserModel.email == str(email))
        return self._session.scalars(statement).first() is not None

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_admin=model.is_admin,
            actor_type=ActorType(model.actor_type),
            created_at=ensure_utc(model.created_at),
        )
