import pytest

from auth_service.application.dto import LoginInput, RegisterUserInput
from auth_service.application.use_cases.login_user import LoginUserUseCase
from auth_service.application.use_cases.register_user import RegisterUserUseCase
from auth_service.domain.exceptions import InactiveUserError, InvalidCredentialsError


@pytest.fixture
def registered_user(user_repository, password_hasher):
    RegisterUserUseCase(user_repository, password_hasher).execute(
        RegisterUserInput(email="user@example.com", password="Str0ngPass")
    )


@pytest.fixture
def use_case(user_repository, token_repository, password_hasher, token_provider):
    counter = iter(["access-jti-1", "refresh-jti-1", "access-jti-2", "refresh-jti-2"])
    return LoginUserUseCase(
        user_repository, token_repository, password_hasher, token_provider, jti_factory=lambda: next(counter)
    )


class TestLoginUserUseCase:
    def test_valid_credentials_return_a_token_pair(self, use_case, registered_user):
        result = use_case.execute(LoginInput(email="user@example.com", password="Str0ngPass"))

        assert result.token_type == "bearer"
        assert result.access_token
        assert result.refresh_token
        assert result.expires_in > 0

    def test_tokens_are_persisted_for_later_validation(self, use_case, registered_user, token_repository):
        use_case.execute(LoginInput(email="user@example.com", password="Str0ngPass"))

        assert token_repository.get_by_jti("access-jti-1") is not None
        assert token_repository.get_by_jti("refresh-jti-1") is not None

    def test_unknown_email_raises_invalid_credentials(self, use_case):
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(LoginInput(email="ghost@example.com", password="Str0ngPass"))

    def test_wrong_password_raises_invalid_credentials(self, use_case, registered_user):
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(LoginInput(email="user@example.com", password="WrongPass1"))

    def test_malformed_email_raises_invalid_credentials_not_invalid_email(self, use_case):
        # Prevents user-enumeration: email-format errors must look identical to bad credentials.
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(LoginInput(email="not-an-email", password="Str0ngPass"))

    def test_inactive_user_cannot_login(self, use_case, registered_user, user_repository):
        from dataclasses import replace

        from auth_service.domain.value_objects.email import Email

        user = user_repository.get_by_email(Email("user@example.com"))
        user_repository.force_save(replace(user, is_active=False))

        with pytest.raises(InactiveUserError):
            use_case.execute(LoginInput(email="user@example.com", password="Str0ngPass"))
