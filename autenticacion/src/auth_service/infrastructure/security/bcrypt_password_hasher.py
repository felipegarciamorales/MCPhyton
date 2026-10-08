from passlib.context import CryptContext

from auth_service.application.ports.password_hasher import PasswordHasher

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BcryptPasswordHasher(PasswordHasher):
    """Password hasher backed by bcrypt (via passlib)."""

    def hash(self, plain_password: str) -> str:
        return _pwd_context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return _pwd_context.verify(plain_password, hashed_password)
        except ValueError:
            return False
