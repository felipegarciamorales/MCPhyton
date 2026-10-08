import pytest

from auth_service.domain.exceptions import InvalidEmailError
from auth_service.domain.value_objects.email import Email


class TestEmail:
    def test_valid_email_is_normalized_to_lowercase(self):
        email = Email("  User@Example.COM  ")

        assert str(email) == "user@example.com"

    @pytest.mark.parametrize(
        "raw_value",
        [
            "",
            "   ",
            "not-an-email",
            "missing-domain@",
            "@missing-local.com",
            "no-at-sign.com",
            "user@no-dot",
        ],
    )
    def test_invalid_email_raises(self, raw_value):
        with pytest.raises(InvalidEmailError):
            Email(raw_value)

    def test_equal_emails_with_different_case_are_equal(self):
        assert Email("Test@Example.com") == Email("test@example.com")
