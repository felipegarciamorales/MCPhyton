import pytest

from auth_service.domain.exceptions import WeakPasswordError
from auth_service.domain.value_objects.password import MAX_LENGTH, MIN_LENGTH, PlainPassword


class TestPlainPassword:
    def test_valid_password_is_accepted(self):
        PlainPassword("Str0ngPass")

    def test_password_shorter_than_minimum_is_rejected(self):
        with pytest.raises(WeakPasswordError):
            PlainPassword("a1a1a1a")  # 7 chars, one below MIN_LENGTH

    def test_password_at_minimum_length_boundary_is_accepted(self):
        value = "a1a1a1a1"  # exactly MIN_LENGTH characters
        assert len(value) == MIN_LENGTH
        PlainPassword(value)

    def test_password_at_maximum_length_boundary_is_accepted(self):
        value = ("a1" * (MAX_LENGTH // 2))[:MAX_LENGTH]
        assert len(value) == MAX_LENGTH
        PlainPassword(value)

    def test_password_exceeding_maximum_length_boundary_is_rejected(self):
        value = ("a1" * (MAX_LENGTH // 2 + 1))[: MAX_LENGTH + 1]
        assert len(value) == MAX_LENGTH + 1
        with pytest.raises(WeakPasswordError):
            PlainPassword(value)

    def test_password_without_digit_is_rejected(self):
        with pytest.raises(WeakPasswordError):
            PlainPassword("NoDigitsHere")

    def test_password_without_letter_is_rejected(self):
        with pytest.raises(WeakPasswordError):
            PlainPassword("12345678")
