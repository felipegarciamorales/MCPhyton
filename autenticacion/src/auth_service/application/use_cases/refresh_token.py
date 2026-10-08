import uuid
from typing import Callable

from auth_service.application.dto import RefreshTokenInput, TokenPairOutput
from auth_service.application.ports.token_provider import TokenProvider, TokenSubject
from auth_service.domain.entities.token import Token, TokenType
from auth_service.domain.exceptions import (
    InactiveUserError,
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
    UserNotFoundError,
)
from auth_service.domain.repositories.token_repository import TokenRepository
from auth_service.domain.repositories.user_repository import UserRepository
from auth_service.shared.clock import utc_now


class RefreshTokenUseCase:
    """Rotates a refresh token: validates it, revokes it, and issues a new pair."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        token_provider: TokenProvider,
        jti_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._token_provider = token_provider
        self._jti_factory = jti_factory

    def execute(self, data: RefreshTokenInput) -> TokenPairOutput:
        decoded = self._token_provider.decode(data.refresh_token)

        if decoded.token_type is not TokenType.REFRESH:
            raise InvalidTokenError("Provided token is not a refresh token")

        stored = self._token_repository.get_by_jti(decoded.jti)
        if stored is None:
            raise InvalidTokenError("Refresh token is unknown")
        if stored.revoked:
            raise TokenRevokedError("Refresh token has been revoked")
        if stored.is_expired():
            raise TokenExpiredError("Refresh token has expired")

        user = self._user_repository.get_by_id(decoded.user_id)
        if user is None:
            raise UserNotFoundError("User associated with token no longer exists")
        if not user.is_active:
            raise InactiveUserError("User account is inactive")

        # Rotate: revoke the used refresh token so it cannot be replayed.
        self._token_repository.revoke(decoded.jti)

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
