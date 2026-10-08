from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from auth_service.domain.value_objects.email import Email
from auth_service.shared.clock import utc_now


class ActorType(str, Enum):
    """Who/what the account represents -- carried in the JWT `aud` claim."""

    HUMAN = "human"
    AGENT = "agent"


@dataclass
class User:
    """Aggregate root representing an account holder."""

    email: Email
    hashed_password: str
    id: Optional[int] = None
    is_active: bool = True
    is_admin: bool = False
    actor_type: ActorType = ActorType.HUMAN
    created_at: datetime = field(default_factory=utc_now)

    @property
    def permissions(self) -> List[str]:
        """Role-derived permission set embedded in issued tokens."""
        return ["user", "admin"] if self.is_admin else ["user"]
