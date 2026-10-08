"""Domain-level errors. These are framework-agnostic and raised by entities,
value objects and application use cases. The presentation layer maps them to
HTTP responses.
"""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class InvalidEmailError(DomainError):
    pass


class InvalidActorTypeError(DomainError):
    pass


class WeakPasswordError(DomainError):
    pass


class UserAlreadyExistsError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass


class InactiveUserError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class InvalidTokenError(DomainError):
    pass


class TokenExpiredError(DomainError):
    pass


class TokenRevokedError(DomainError):
    pass
