from auth_service.domain.entities.user import ActorType, User
from auth_service.domain.value_objects.email import Email


def _user(**overrides) -> User:
    defaults = dict(email=Email("user@example.com"), hashed_password="hashed")
    defaults.update(overrides)
    return User(**defaults)


class TestUser:
    def test_defaults_to_non_admin_human(self):
        user = _user()

        assert user.is_admin is False
        assert user.actor_type is ActorType.HUMAN

    def test_regular_user_permissions(self):
        user = _user(is_admin=False)

        assert user.permissions == ["user"]

    def test_admin_user_permissions_include_both_roles(self):
        user = _user(is_admin=True)

        assert user.permissions == ["user", "admin"]

    def test_agent_actor_type_is_preserved(self):
        user = _user(actor_type=ActorType.AGENT)

        assert user.actor_type is ActorType.AGENT
