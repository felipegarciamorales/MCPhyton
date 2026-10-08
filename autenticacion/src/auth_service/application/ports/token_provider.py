from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

from auth_service.domain.entities.token import TokenType


@dataclass(frozen=True)
class TokenSubject:
    """User-derived claims embedded into an issued JWT."""

    user_id: int
    email: str
    is_admin: bool
    actor_type: str
    permissions: List[str]


@dataclass(frozen=True)
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime


@dataclass(frozen=True)
class DecodedToken:
    user_id: int
    jti: str
    token_type: TokenType
    expires_at: datetime
    is_admin: bool
    aud: str
    permissions: List[str]


class TokenProvider(ABC):
    """Port for issuing and decoding signed JWT access/refresh tokens."""

    @abstractmethod
    def issue_access_token(self, subject: TokenSubject, jti: str) -> IssuedToken: ...

    @abstractmethod
    def issue_refresh_token(self, subject: TokenSubject, jti: str) -> IssuedToken: ...

    @abstractmethod
    def decode(self, token: str) -> DecodedToken:
        """Decode and verify a JWT.

        Raises:
            TokenExpiredError: if the token's signature is valid but it has expired.
            InvalidTokenError: if the token is malformed, tampered with, or has an
                invalid signature or payload.
        """
