import re
from dataclasses import dataclass

from auth_service.domain.exceptions import InvalidEmailError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    """Value object guaranteeing a normalized, syntactically valid email address."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized or not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(f"'{self.value}' is not a valid email address")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
