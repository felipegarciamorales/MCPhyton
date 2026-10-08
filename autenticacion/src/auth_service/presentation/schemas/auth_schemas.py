from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from auth_service.domain.value_objects.password import MAX_LENGTH, MIN_LENGTH


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_LENGTH, max_length=MAX_LENGTH)
    # `is_admin` is intentionally not exposed here to avoid privilege escalation
    # via public self-registration.
    actor_type: Literal["human", "agent"] = "human"


class RegisterResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    actor_type: str
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_LENGTH)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ValidateRequest(BaseModel):
    token: str


class ValidateResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None
    is_admin: Optional[bool] = None
    aud: Optional[str] = None
    permissions: Optional[List[str]] = None
