from abc import ABC, abstractmethod
from typing import Optional

from auth_service.domain.entities.token import Token


class TokenRepository(ABC):
    """Port defining persistence operations for issued Token records."""

    @abstractmethod
    def add(self, token: Token) -> Token: ...

    @abstractmethod
    def get_by_jti(self, jti: str) -> Optional[Token]: ...

    @abstractmethod
    def revoke(self, jti: str) -> None: ...

    @abstractmethod
    def revoke_all_for_user(self, user_id: int, token_type: Optional[str] = None) -> None: ...
