import pytest
from freezegun import freeze_time

from auth_service.application.dto import LoginInput, RefreshTokenInput, RegisterUserInput
from auth_service.application.use_cases.login_user import LoginUserUseCase
from auth_service.application.use_cases.refresh_token import RefreshTokenUseCase
from auth_service.application.use_cases.register_user import RegisterUserUseCase
from auth_service.domain.exceptions import InvalidTokenError, TokenExpiredError, TokenRevokedError, UserNotFoundError


@pytest.fixture
def logged_in_tokens(user_repository, token_repository, password_hasher, token_provider):
    RegisterUserUseCase(user_repository, password_hasher).execute(
        RegisterUserInput(email="user@example.com", password="Str0ngPass")
    )
    counter = iter(["access-1", "refresh-1"])
    login_use_case = LoginUserUseCase(
        user_repository, token_repository, password_hasher, token_provider, jti_factory=lambda: next(counter)
    )
    with freeze_time("2030-01-01 00:00:00"):
        return login_use_case.execute(LoginInput(email="user@example.com", password="Str0ngPass"))


@pytest.fixture
def use_case(user_repository, token_repository, token_provider):
    counter = iter(["access-2", "refresh-2"])
    return RefreshTokenUseCase(user_repository, token_repository, token_provider, jti_factory=lambda: next(counter))


class TestRefreshTokenUseCase:
    def test_valid_refresh_token_returns_a_new_pair(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 00:10:00"):
            result = use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.refresh_token))

        assert result.access_token != logged_in_tokens.access_token
        assert result.refresh_token != logged_in_tokens.refresh_token

    def test_used_refresh_token_is_revoked_after_rotation(self, use_case, logged_in_tokens, token_repository):
        with freeze_time("2030-01-01 00:10:00"):
            use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.refresh_token))

        assert token_repository.get_by_jti("refresh-1").revoked is True

    def test_reusing_a_rotated_refresh_token_is_rejected(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 00:10:00"):
            use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.refresh_token))

            with pytest.raises(TokenRevokedError):
                use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.refresh_token))

    def test_using_an_access_token_as_a_refresh_token_is_rejected(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 00:10:00"):
            with pytest.raises(InvalidTokenError):
                use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.access_token))

    def test_unknown_token_is_rejected(self, use_case):
        with pytest.raises(InvalidTokenError):
            use_case.execute(RefreshTokenInput(refresh_token="does-not-exist"))

    def test_expired_refresh_token_is_rejected(self, use_case, logged_in_tokens):
        with freeze_time("2999-01-01 00:00:00"):
            with pytest.raises(TokenExpiredError):
                use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.refresh_token))

    def test_refresh_fails_when_user_no_longer_exists(self, use_case, logged_in_tokens, user_repository):
        user_repository.delete(1)

        with freeze_time("2030-01-01 00:10:00"):
            with pytest.raises(UserNotFoundError):
                use_case.execute(RefreshTokenInput(refresh_token=logged_in_tokens.refresh_token))
