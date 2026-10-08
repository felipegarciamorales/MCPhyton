import pytest
from freezegun import freeze_time

from auth_service.application.ports.token_provider import TokenSubject
from auth_service.config import Settings
from auth_service.domain.entities.token import TokenType
from auth_service.domain.exceptions import InvalidTokenError, TokenExpiredError
from auth_service.infrastructure.security.jwt_token_provider import JwtTokenProvider


def _subject(user_id=1, email="a@example.com", is_admin=False, actor_type="human", permissions=None):
    return TokenSubject(
        user_id=user_id,
        email=email,
        is_admin=is_admin,
        actor_type=actor_type,
        permissions=permissions if permissions is not None else ["user"],
    )


@pytest.fixture
def settings():
    return Settings(
        jwt_secret_key="test-secret-key-at-least-32-bytes-long",
        access_token_expire_minutes=60,
        refresh_token_expire_minutes=120,
    )


@pytest.fixture
def provider(settings):
    return JwtTokenProvider(settings)


class TestJwtTokenProvider:
    def test_issued_access_token_decodes_to_the_same_claims(self, provider):
        issued = provider.issue_access_token(_subject(user_id=42), "jti-1")

        decoded = provider.decode(issued.token)

        assert decoded.user_id == 42
        assert decoded.jti == "jti-1"
        assert decoded.token_type is TokenType.ACCESS

    def test_issued_refresh_token_has_the_refresh_type(self, provider):
        issued = provider.issue_refresh_token(_subject(user_id=42), "jti-2")

        decoded = provider.decode(issued.token)

        assert decoded.token_type is TokenType.REFRESH

    def test_admin_claim_is_carried_through(self, provider):
        issued = provider.issue_access_token(_subject(is_admin=True, permissions=["user", "admin"]), "jti-admin")

        decoded = provider.decode(issued.token)

        assert decoded.is_admin is True
        assert decoded.permissions == ["user", "admin"]

    def test_non_admin_claim_is_carried_through(self, provider):
        issued = provider.issue_access_token(_subject(is_admin=False, permissions=["user"]), "jti-user")

        decoded = provider.decode(issued.token)

        assert decoded.is_admin is False
        assert decoded.permissions == ["user"]

    def test_aud_claim_reflects_the_actor_type(self, provider):
        issued = provider.issue_access_token(_subject(actor_type="agent"), "jti-agent")

        decoded = provider.decode(issued.token)

        assert decoded.aud == "agent"

    def test_tampered_token_is_rejected(self, provider):
        issued = provider.issue_access_token(_subject(), "jti-3")
        tampered = issued.token[:-1] + ("A" if issued.token[-1] != "A" else "B")

        with pytest.raises(InvalidTokenError):
            provider.decode(tampered)

    def test_token_signed_with_a_different_secret_is_rejected(self, provider):
        other_provider = JwtTokenProvider(
            Settings(
                jwt_secret_key="another-secret-key-at-least-32-bytes",
                access_token_expire_minutes=60,
                refresh_token_expire_minutes=120,
            )
        )
        issued = other_provider.issue_access_token(_subject(), "jti-4")

        with pytest.raises(InvalidTokenError):
            provider.decode(issued.token)

    def test_garbage_string_is_rejected(self, provider):
        with pytest.raises(InvalidTokenError):
            provider.decode("not-a-jwt-at-all")

    def test_token_expires_after_the_configured_number_of_minutes(self, provider):
        with freeze_time("2030-01-01 00:00:00"):
            issued = provider.issue_access_token(_subject(), "jti-5")

        with freeze_time("2030-01-01 01:00:01"):
            with pytest.raises(TokenExpiredError):
                provider.decode(issued.token)

    def test_token_is_still_valid_one_second_before_expiration_boundary(self, provider):
        with freeze_time("2030-01-01 00:00:00"):
            issued = provider.issue_access_token(_subject(), "jti-6")

        with freeze_time("2030-01-01 00:59:59"):
            decoded = provider.decode(issued.token)

        assert decoded.jti == "jti-6"

