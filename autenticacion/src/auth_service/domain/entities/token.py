from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from auth_service.shared.clock import utc_now


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class Token:
    """Represents an issued JWT tracked server-side to support revocation."""

    jti: str
    user_id: int
    token_type: TokenType
    expires_at: datetime
    id: Optional[int] = None
    revoked: bool = False
    created_at: datetime = field(default_factory=utc_now)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        current = now or utc_now()
        return current >= self.expires_at

    def is_valid(self, now: Optional[datetime] = None) -> bool:
        return not self.revoked and not self.is_expired(now)
