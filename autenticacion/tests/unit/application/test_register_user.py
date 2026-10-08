import pytest

from auth_service.application.dto import RegisterUserInput
from auth_service.application.use_cases.register_user import RegisterUserUseCase
from auth_service.domain.exceptions import (
    InvalidActorTypeError,
    InvalidEmailError,
    UserAlreadyExistsError,
    WeakPasswordError,
)
from auth_service.domain.value_objects.email import Email


@pytest.fixture
def use_case(user_repository, password_hasher):
    return RegisterUserUseCase(user_repository, password_hasher)


class TestRegisterUserUseCase:
    def test_registers_a_new_user_successfully(self, use_case):
        result = use_case.execute(RegisterUserInput(email="new.user@example.com", password="Str0ngPass"))

        assert result.id == 1
        assert result.email == "new.user@example.com"

    def test_new_user_defaults_to_non_admin_human(self, use_case):
        result = use_case.execute(RegisterUserInput(email="new.user@example.com", password="Str0ngPass"))

        assert result.is_admin is False
        assert result.actor_type == "human"

    def test_user_can_self_register_as_an_agent(self, use_case):
        result = use_case.execute(
            RegisterUserInput(email="bot@example.com", password="Str0ngPass", actor_type="agent")
        )

        assert result.actor_type == "agent"
        assert result.is_admin is False

    def test_invalid_actor_type_is_rejected(self, use_case):
        with pytest.raises(InvalidActorTypeError):
            use_case.execute(
                RegisterUserInput(email="new.user@example.com", password="Str0ngPass", actor_type="robot")
            )

    def test_password_is_hashed_before_storage(self, use_case, user_repository):
        use_case.execute(RegisterUserInput(email="user@example.com", password="Str0ngPass"))

        stored = user_repository.get_by_email(Email("user@example.com"))
        assert stored.hashed_password != "Str0ngPass"
        assert stored.hashed_password == "hashed:Str0ngPass"

    def test_duplicate_email_raises_user_already_exists(self, use_case):
        use_case.execute(RegisterUserInput(email="dup@example.com", password="Str0ngPass"))

        with pytest.raises(UserAlreadyExistsError):
            use_case.execute(RegisterUserInput(email="dup@example.com", password="An0therPass"))

    def test_duplicate_email_detection_is_case_insensitive(self, use_case):
        use_case.execute(RegisterUserInput(email="dup@example.com", password="Str0ngPass"))

        with pytest.raises(UserAlreadyExistsError):
            use_case.execute(RegisterUserInput(email="DUP@Example.com", password="An0therPass"))

    def test_invalid_email_is_rejected(self, use_case):
        with pytest.raises(InvalidEmailError):
            use_case.execute(RegisterUserInput(email="not-an-email", password="Str0ngPass"))

    def test_weak_password_is_rejected(self, use_case):
        with pytest.raises(WeakPasswordError):
            use_case.execute(RegisterUserInput(email="user2@example.com", password="weak"))
