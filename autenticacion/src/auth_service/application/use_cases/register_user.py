from auth_service.application.dto import RegisterUserInput, RegisterUserOutput
from auth_service.application.ports.password_hasher import PasswordHasher
from auth_service.domain.entities.user import ActorType, User
from auth_service.domain.exceptions import InvalidActorTypeError, UserAlreadyExistsError
from auth_service.domain.repositories.user_repository import UserRepository
from auth_service.domain.value_objects.email import Email
from auth_service.domain.value_objects.password import PlainPassword


class RegisterUserUseCase:
    """Registers a new user, enforcing email/password policy and uniqueness.

    Note: `is_admin` is intentionally not settable here -- granting it through a
    public self-registration endpoint would be a privilege-escalation hole.
    """

    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    def execute(self, data: RegisterUserInput) -> RegisterUserOutput:
        email = Email(data.email)
        PlainPassword(data.password)  # raises WeakPasswordError if the policy is violated

        try:
            actor_type = ActorType(data.actor_type)
        except ValueError as exc:
            raise InvalidActorTypeError(f"'{data.actor_type}' is not a valid actor type") from exc

        if self._user_repository.exists_by_email(email):
            raise UserAlreadyExistsError(f"A user with email '{email}' already exists")

        hashed_password = self._password_hasher.hash(data.password)
        user = self._user_repository.add(User(email=email, hashed_password=hashed_password, actor_type=actor_type))

        return RegisterUserOutput(
            id=user.id,
            email=str(user.email),
            is_admin=user.is_admin,
            actor_type=user.actor_type.value,
            created_at=user.created_at,
        )
