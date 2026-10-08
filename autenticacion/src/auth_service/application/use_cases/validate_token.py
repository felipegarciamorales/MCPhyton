from auth_service.application.dto import ValidateTokenInput, ValidateTokenOutput
from auth_service.application.ports.token_provider import TokenProvider
from auth_service.domain.entities.token import TokenType
from auth_service.domain.exceptions import InvalidTokenError, TokenExpiredError
from auth_service.domain.repositories.token_repository import TokenRepository
from auth_service.domain.repositories.user_repository import UserRepository


class ValidateTokenUseCase:
    """Validates an access token's signature, expiration and revocation status.

    This use case never raises for "the token is invalid" scenarios; it always
    returns a ValidateTokenOutput so the API can respond with 200 OK and a
    `valid` flag, which is the expected contract for a validation endpoint.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        token_provider: TokenProvider,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._token_provider = token_provider

    def execute(self, data: ValidateTokenInput) -> ValidateTokenOutput:
        try:
            decoded = self._token_provider.decode(data.token)
        except TokenExpiredError:
            return ValidateTokenOutput(valid=False, reason="Token has expired")
        except InvalidTokenError:
            return ValidateTokenOutput(valid=False, reason="Token is malformed or has an invalid signature")

        if decoded.token_type is not TokenType.ACCESS:
            return ValidateTokenOutput(valid=False, reason="Only access tokens can be validated")

        stored = self._token_repository.get_by_jti(decoded.jti)
        if stored is None:
            return ValidateTokenOutput(valid=False, reason="Token is unknown")
        if stored.revoked:
            return ValidateTokenOutput(valid=False, reason="Token has been revoked")
        if stored.is_expired():
            return ValidateTokenOutput(valid=False, reason="Token has expired")

        user = self._user_repository.get_by_id(decoded.user_id)
        if user is None or not user.is_active:
            return ValidateTokenOutput(valid=False, reason="User is not available")

        return ValidateTokenOutput(
            valid=True,
            user_id=user.id,
            email=str(user.email),
            expires_at=stored.expires_at,
            is_admin=decoded.is_admin,
            aud=decoded.aud,
            permissions=decoded.permissions,
        )
