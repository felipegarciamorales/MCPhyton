from datetime import timedelta

import pytest

from auth_service.domain.entities.token import Token, TokenType
from auth_service.domain.entities.user import User
from auth_service.domain.value_objects.email import Email
from auth_service.infrastructure.persistence.sqlite_token_repository import SqliteTokenRepository
from auth_service.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
from auth_service.shared.clock import utc_now


@pytest.fixture
def user_id(db_session):
    repo = SqliteUserRepository(db_session)
    return repo.add(User(email=Email("user@example.com"), hashed_password="hashed")).id


@pytest.fixture
def repository(db_session):
    return SqliteTokenRepository(db_session)


class TestSqliteTokenRepository:
    def test_add_persists_a_token(self, repository, user_id):
        token = Token(
            jti="jti-1", user_id=user_id, token_type=TokenType.ACCESS, expires_at=utc_now() + timedelta(hours=1)
        )

        created = repository.add(token)

        assert created.id is not None

    def test_get_by_jti_returns_the_persisted_token(self, repository, user_id):
        repository.add(
            Token(
                jti="jti-1",
                user_id=user_id,
                token_type=TokenType.ACCESS,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )

        found = repository.get_by_jti("jti-1")

        assert found is not None
        assert found.token_type is TokenType.ACCESS

    def test_get_by_jti_returns_none_for_an_unknown_jti(self, repository):
        assert repository.get_by_jti("does-not-exist") is None

    def test_revoke_marks_the_token_as_revoked(self, repository, user_id):
        repository.add(
            Token(
                jti="jti-1",
                user_id=user_id,
                token_type=TokenType.REFRESH,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )

        repository.revoke("jti-1")

        assert repository.get_by_jti("jti-1").revoked is True

    def test_revoke_all_for_user_revokes_only_the_matching_token_type(self, repository, user_id):
        repository.add(
            Token(
                jti="jti-1",
                user_id=user_id,
                token_type=TokenType.REFRESH,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        repository.add(
            Token(
                jti="jti-2",
                user_id=user_id,
                token_type=TokenType.ACCESS,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )

        repository.revoke_all_for_user(user_id, token_type=TokenType.REFRESH.value)

        assert repository.get_by_jti("jti-1").revoked is True
        assert repository.get_by_jti("jti-2").revoked is False
