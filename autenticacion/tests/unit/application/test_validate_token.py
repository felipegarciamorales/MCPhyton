import pytest
from freezegun import freeze_time

from auth_service.application.dto import LoginInput, RegisterUserInput, ValidateTokenInput
from auth_service.application.use_cases.login_user import LoginUserUseCase
from auth_service.application.use_cases.register_user import RegisterUserUseCase
from auth_service.application.use_cases.validate_token import ValidateTokenUseCase


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
    return ValidateTokenUseCase(user_repository, token_repository, token_provider)


class TestValidateTokenUseCase:
    def test_valid_access_token_is_reported_as_valid(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 00:10:00"):
            result = use_case.execute(ValidateTokenInput(token=logged_in_tokens.access_token))

        assert result.valid is True
        assert result.email == "user@example.com"

    def test_valid_token_exposes_admin_aud_and_permissions_claims(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 00:10:00"):
            result = use_case.execute(ValidateTokenInput(token=logged_in_tokens.access_token))

        assert result.is_admin is False
        assert result.aud == "human"
        assert result.permissions == ["user"]

    def test_refresh_token_cannot_be_validated_as_an_access_token(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 00:10:00"):
            result = use_case.execute(ValidateTokenInput(token=logged_in_tokens.refresh_token))

        assert result.valid is False

    def test_unknown_token_is_invalid(self, use_case):
        result = use_case.execute(ValidateTokenInput(token="garbage"))

        assert result.valid is False
        assert result.reason

    def test_revoked_token_is_invalid(self, use_case, logged_in_tokens, token_repository):
        token_repository.revoke("access-1")

        with freeze_time("2030-01-01 00:10:00"):
            result = use_case.execute(ValidateTokenInput(token=logged_in_tokens.access_token))

        assert result.valid is False

    def test_token_one_second_before_expiration_boundary_is_valid(self, use_case, logged_in_tokens):
        # FakeTokenProvider defaults to a 60 minute access token lifetime.
        with freeze_time("2030-01-01 00:59:59"):
            result = use_case.execute(ValidateTokenInput(token=logged_in_tokens.access_token))

        assert result.valid is True

    def test_token_at_exact_expiration_instant_is_invalid(self, use_case, logged_in_tokens):
        with freeze_time("2030-01-01 01:00:00"):
            result = use_case.execute(ValidateTokenInput(token=logged_in_tokens.access_token))

        assert result.valid is False
