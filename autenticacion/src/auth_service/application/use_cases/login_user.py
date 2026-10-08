import uuid
from typing import Callable

from auth_service.application.dto import LoginInput, TokenPairOutput
from auth_service.application.ports.password_hasher import PasswordHasher
from auth_service.application.ports.token_provider import TokenProvider, TokenSubject
from auth_service.domain.entities.token import Token, TokenType
from auth_service.domain.exceptions import InactiveUserError, InvalidCredentialsError
from auth_service.domain.repositories.token_repository import TokenRepository
from auth_service.domain.repositories.user_repository import UserRepository
from auth_service.domain.value_objects.email import Email
from auth_service.shared.clock import utc_now


class LoginUserUseCase:
    """Authenticates a user and issues a fresh access/refresh token pair."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        password_hasher: PasswordHasher,
        token_provider: TokenProvider,
        jti_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._password_hasher = password_hasher
        self._token_provider = token_provider
        self._jti_factory = jti_factory

    def execute(self, data: LoginInput) -> TokenPairOutput:
        try:
            email = Email(data.email)
        except Exception as exc:
            # Do not leak whether the failure was email-format or credential related.
            raise InvalidCredentialsError("Invalid email or password") from exc

        user = self._user_repository.get_by_email(email)
        if user is None or not self._password_hasher.verify(data.password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        subject = TokenSubject(
            user_id=user.id,
            email=str(user.email),
            is_admin=user.is_admin,
            actor_type=user.actor_type.value,
            permissions=user.permissions,
        )
        access = self._token_provider.issue_access_token(subject, self._jti_factory())
        refresh = self._token_provider.issue_refresh_token(subject, self._jti_factory())

        self._token_repository.add(
            Token(jti=access.jti, user_id=user.id, token_type=TokenType.ACCESS, expires_at=access.expires_at)
        )
        self._token_repository.add(
            Token(jti=refresh.jti, user_id=user.id, token_type=TokenType.REFRESH, expires_at=refresh.expires_at)
        )

        expires_in = int((access.expires_at - utc_now()).total_seconds())
        return TokenPairOutput(
            access_token=access.token,
            refresh_token=refresh.token,
            token_type="bearer",
            expires_in=expires_in,
        )
