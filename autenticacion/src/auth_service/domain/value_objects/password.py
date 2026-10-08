from dataclasses import dataclass

from auth_service.domain.exceptions import WeakPasswordError

MIN_LENGTH = 8
# bcrypt (used for hashing) ignores/errors on bytes beyond 72, so this is both
# a usability policy and a hard technical ceiling.
MAX_LENGTH = 72


@dataclass(frozen=True)
class PlainPassword:
    """A password supplied by the user, validated against the password policy."""

    value: str

    def __post_init__(self) -> None:
        if len(self.value) < MIN_LENGTH:
            raise WeakPasswordError(f"Password must be at least {MIN_LENGTH} characters long")
        if len(self.value) > MAX_LENGTH:
            raise WeakPasswordError(f"Password must be at most {MAX_LENGTH} characters long")
        if not any(char.isdigit() for char in self.value):
            raise WeakPasswordError("Password must contain at least one digit")
        if not any(char.isalpha() for char in self.value):
            raise WeakPasswordError("Password must contain at least one letter")


@dataclass(frozen=True)
class HashedPassword:
    """Wraps an already-hashed password so plain and hashed values can't be mixed up."""

    value: str
