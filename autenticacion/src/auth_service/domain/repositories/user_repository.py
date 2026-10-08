from abc import ABC, abstractmethod
from typing import Optional

from auth_service.domain.entities.user import User
from auth_service.domain.value_objects.email import Email


class UserRepository(ABC):
    """Port defining persistence operations for User aggregates."""

    @abstractmethod
    def add(self, user: User) -> User: ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[User]: ...

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool: ...
