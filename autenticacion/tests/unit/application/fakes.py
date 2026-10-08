"""Hand-written test doubles implementing the application ports.

Using fakes (rather than mocking frameworks) keeps unit tests fast, readable,
and decoupled from implementation details -- exactly what the ports (DIP)
are meant to enable.
"""

from dataclasses import replace
from datetime import timedelta
from typing import Dict, Optional

from auth_service.application.ports.password_hasher import PasswordHasher
from auth_service.application.ports.token_provider import DecodedToken, IssuedToken, TokenProvider, TokenSubject
from auth_service.domain.entities.token import Token, TokenType
from auth_service.domain.entities.user import User
from auth_service.domain.exceptions import InvalidTokenError, TokenExpiredError
from auth_service.domain.repositories.token_repository import TokenRepository
from auth_service.domain.repositories.user_repository import UserRepository
from auth_service.domain.value_objects.email import Email
from auth_service.shared.clock import utc_now


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: Dict[int, User] = {}
        self._next_id = 1

    def add(self, user: User) -> User:
        stored = replace(user, id=self._next_id)
        self._users[self._next_id] = stored
        self._next_id += 1
        return stored

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def get_by_email(self, email: Email) -> Optional[User]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def exists_by_email(self, email: Email) -> bool:
        return self.get_by_email(email) is not None

    def force_save(self, user: User) -> None:
        """Test-only helper to seed/mutate state without going through add()."""
        self._users[user.id] = user

    def delete(self, user_id: int) -> None:
        """Test-only helper to simulate a user that no longer exists."""
        self._users.pop(user_id, None)


class InMemoryTokenRepository(TokenRepository):
    def __init__(self) -> None:
        self._tokens: Dict[str, Token] = {}

    def add(self, token: Token) -> Token:
        self._tokens[token.jti] = token
        return token

    def get_by_jti(self, jti: str) -> Optional[Token]:
        return self._tokens.get(jti)

    def revoke(self, jti: str) -> None:
        if jti in self._tokens:
            self._tokens[jti] = replace(self._tokens[jti], revoked=True)

    def revoke_all_for_user(self, user_id: int, token_type: Optional[str] = None) -> None:
        for jti, token in list(self._tokens.items()):
            if token.user_id == user_id and (token_type is None or token.token_type.value == token_type):
                self._tokens[jti] = replace(token, revoked=True)


class FakePasswordHasher(PasswordHasher):
    """Deterministic, non-cryptographic hasher for fast, isolated unit tests."""

    def hash(self, plain_password: str) -> str:
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"


class FakeTokenProvider(TokenProvider):
    """In-memory token provider that avoids real JWT encoding for unit tests."""

    def __init__(self, access_expire_minutes: int = 60, refresh_expire_minutes: int = 60 * 24 * 7) -> None:
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_minutes = refresh_expire_minutes
        self._registry: Dict[str, DecodedToken] = {}

    def issue_access_token(self, subject: TokenSubject, jti: str) -> IssuedToken:
        return self._issue(subject, jti, TokenType.ACCESS, self._access_expire_minutes)

    def issue_refresh_token(self, subject: TokenSubject, jti: str) -> IssuedToken:
        return self._issue(subject, jti, TokenType.REFRESH, self._refresh_expire_minutes)

    def decode(self, token: str) -> DecodedToken:
        decoded = self._registry.get(token)
        if decoded is None:
            raise InvalidTokenError("Unknown token")
        if utc_now() >= decoded.expires_at:
            raise TokenExpiredError("Token has expired")
        return decoded

    def _issue(self, subject: TokenSubject, jti: str, token_type: TokenType, expire_minutes: int) -> IssuedToken:
        expires_at = utc_now() + timedelta(minutes=expire_minutes)
        token_str = f"{token_type.value}:{jti}"
        self._registry[token_str] = DecodedToken(
            user_id=subject.user_id,
            jti=jti,
            token_type=token_type,
            expires_at=expires_at,
            is_admin=subject.is_admin,
            aud=subject.actor_type,
            permissions=subject.permissions,
        )
        return IssuedToken(token=token_str, jti=jti, expires_at=expires_at)
