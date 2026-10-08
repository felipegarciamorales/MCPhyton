"""Data transfer objects exchanged between the presentation layer and use cases."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class RegisterUserInput:
    email: str
    password: str
    actor_type: str = "human"


@dataclass(frozen=True)
class RegisterUserOutput:
    id: int
    email: str
    is_admin: bool
    actor_type: str
    created_at: datetime


@dataclass(frozen=True)
class LoginInput:
    email: str
    password: str


@dataclass(frozen=True)
class TokenPairOutput:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass(frozen=True)
class RefreshTokenInput:
    refresh_token: str


@dataclass(frozen=True)
class ValidateTokenInput:
    token: str


@dataclass(frozen=True)
class ValidateTokenOutput:
    valid: bool
    user_id: Optional[int] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    is_admin: Optional[bool] = None
    aud: Optional[str] = None
    permissions: Optional[List[str]] = None
