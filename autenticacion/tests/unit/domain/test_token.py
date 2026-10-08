from datetime import timedelta

from auth_service.domain.entities.token import Token, TokenType
from auth_service.shared.clock import utc_now


class TestToken:
    def test_token_not_expired_before_expiration(self):
        token = Token(jti="abc", user_id=1, token_type=TokenType.ACCESS, expires_at=utc_now() + timedelta(minutes=5))

        assert token.is_expired() is False
        assert token.is_valid() is True

    def test_token_expired_after_expiration(self):
        token = Token(jti="abc", user_id=1, token_type=TokenType.ACCESS, expires_at=utc_now() - timedelta(seconds=1))

        assert token.is_expired() is True
        assert token.is_valid() is False

    def test_token_at_exact_expiration_instant_is_considered_expired(self):
        now = utc_now()
        token = Token(jti="abc", user_id=1, token_type=TokenType.ACCESS, expires_at=now)

        assert token.is_expired(now=now) is True

    def test_token_one_second_before_expiration_boundary_is_valid(self):
        now = utc_now()
        token = Token(jti="abc", user_id=1, token_type=TokenType.ACCESS, expires_at=now)

        assert token.is_expired(now=now - timedelta(seconds=1)) is False

    def test_revoked_token_is_not_valid_even_if_not_expired(self):
        token = Token(
            jti="abc",
            user_id=1,
            token_type=TokenType.REFRESH,
            expires_at=utc_now() + timedelta(hours=1),
            revoked=True,
        )

        assert token.is_valid() is False
