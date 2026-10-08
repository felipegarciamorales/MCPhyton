from datetime import datetime, timedelta, timezone

import jwt

from auth_service.application.ports.token_provider import DecodedToken, IssuedToken, TokenProvider, TokenSubject
from auth_service.config import Settings
from auth_service.domain.entities.token import TokenType
from auth_service.domain.exceptions import InvalidTokenError, TokenExpiredError
from auth_service.shared.clock import utc_now


class JwtTokenProvider(TokenProvider):
    """Issues and decodes JWT access/refresh tokens using PyJWT."""

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire_minutes = settings.access_token_expire_minutes
        self._refresh_expire_minutes = settings.refresh_token_expire_minutes

    def issue_access_token(self, subject: TokenSubject, jti: str) -> IssuedToken:
        return self._issue(subject, jti, TokenType.ACCESS, self._access_expire_minutes)

    def issue_refresh_token(self, subject: TokenSubject, jti: str) -> IssuedToken:
        return self._issue(subject, jti, TokenType.REFRESH, self._refresh_expire_minutes)

    def decode(self, token: str) -> DecodedToken:
        try:
            # `aud` here carries our custom actor-type claim, not a recipient
            # identifier, so PyJWT's built-in audience check must stay off.
            payload = jwt.decode(
                token, self._secret_key, algorithms=[self._algorithm], options={"verify_aud": False}
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError("Token is invalid") from exc

        try:
            return DecodedToken(
                user_id=int(payload["sub"]),
                jti=payload["jti"],
                token_type=TokenType(payload["type"]),
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                is_admin=bool(payload.get("admin", False)),
                aud=payload.get("aud", "human"),
                permissions=list(payload.get("permissions", [])),
            )
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError("Token payload is malformed") from exc

    def _issue(
        self, subject: TokenSubject, jti: str, token_type: TokenType, expire_minutes: int
    ) -> IssuedToken:
        now = utc_now()
        expires_at = now + timedelta(minutes=expire_minutes)
        payload = {
            "sub": str(subject.user_id),
            "email": subject.email,
            "jti": jti,
            "type": token_type.value,
            "admin": subject.is_admin,
            "aud": subject.actor_type,
            "permissions": subject.permissions,
            "iat": now,
            "exp": expires_at,
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return IssuedToken(token=token, jti=jti, expires_at=expires_at)
