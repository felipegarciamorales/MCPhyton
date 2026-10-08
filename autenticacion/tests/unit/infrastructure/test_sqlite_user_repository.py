import pytest

from auth_service.domain.entities.user import ActorType, User
from auth_service.domain.value_objects.email import Email
from auth_service.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository


@pytest.fixture
def repository(db_session):
    return SqliteUserRepository(db_session)


class TestSqliteUserRepository:
    def test_add_persists_and_assigns_an_id(self, repository):
        created = repository.add(User(email=Email("user@example.com"), hashed_password="hashed"))

        assert created.id is not None

    def test_add_persists_admin_flag_and_actor_type(self, repository):
        created = repository.add(
            User(email=Email("admin@example.com"), hashed_password="hashed", is_admin=True, actor_type=ActorType.AGENT)
        )

        found = repository.get_by_id(created.id)

        assert found.is_admin is True
        assert found.actor_type is ActorType.AGENT

    def test_defaults_persist_as_non_admin_human(self, repository):
        created = repository.add(User(email=Email("user@example.com"), hashed_password="hashed"))

        found = repository.get_by_id(created.id)

        assert found.is_admin is False
        assert found.actor_type is ActorType.HUMAN

    def test_get_by_id_returns_the_persisted_user(self, repository):
        created = repository.add(User(email=Email("user@example.com"), hashed_password="hashed"))

        found = repository.get_by_id(created.id)

        assert found is not None
        assert str(found.email) == "user@example.com"

    def test_get_by_id_returns_none_for_an_unknown_id(self, repository):
        assert repository.get_by_id(999) is None

    def test_get_by_email_is_case_insensitive(self, repository):
        repository.add(User(email=Email("User@Example.com"), hashed_password="hashed"))

        assert repository.get_by_email(Email("user@example.com")) is not None

    def test_exists_by_email_is_true_after_creation(self, repository):
        repository.add(User(email=Email("user@example.com"), hashed_password="hashed"))

        assert repository.exists_by_email(Email("user@example.com")) is True

    def test_exists_by_email_is_false_when_absent(self, repository):
        assert repository.exists_by_email(Email("missing@example.com")) is False
