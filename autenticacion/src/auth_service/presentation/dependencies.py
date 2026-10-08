"""FastAPI dependency providers wiring ports to their infrastructure implementations."""

from typing import Generator, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from auth_service.application.ports.password_hasher import PasswordHasher
from auth_service.application.ports.token_provider import TokenProvider
from auth_service.application.use_cases.login_user import LoginUserUseCase
from auth_service.application.use_cases.refresh_token import RefreshTokenUseCase
from auth_service.application.use_cases.register_user import RegisterUserUseCase
from auth_service.application.use_cases.validate_token import ValidateTokenUseCase
from auth_service.config import Settings, get_settings
from auth_service.domain.repositories.token_repository import TokenRepository
from auth_service.domain.repositories.user_repository import UserRepository
from auth_service.infrastructure.persistence.database import SessionLocal
from auth_service.infrastructure.persistence.sqlite_token_repository import SqliteTokenRepository
from auth_service.infrastructure.persistence.sqlite_user_repository import SqliteUserRepository
from auth_service.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher
from auth_service.infrastructure.security.jwt_token_provider import JwtTokenProvider


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_user_repository(session: Session = Depends(get_session)) -> UserRepository:
    return SqliteUserRepository(session)


def get_token_repository(session: Session = Depends(get_session)) -> TokenRepository:
    return SqliteTokenRepository(session)


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_token_provider(settings: Optional[Settings] = Depends(get_settings)) -> TokenProvider:
    return JwtTokenProvider(settings)


def get_register_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repository, password_hasher)


def get_login_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    token_repository: TokenRepository = Depends(get_token_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_provider: TokenProvider = Depends(get_token_provider),
) -> LoginUserUseCase:
    return LoginUserUseCase(user_repository, token_repository, password_hasher, token_provider)


def get_refresh_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    token_repository: TokenRepository = Depends(get_token_repository),
    token_provider: TokenProvider = Depends(get_token_provider),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(user_repository, token_repository, token_provider)


def get_validate_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    token_repository: TokenRepository = Depends(get_token_repository),
    token_provider: TokenProvider = Depends(get_token_provider),
) -> ValidateTokenUseCase:
    return ValidateTokenUseCase(user_repository, token_repository, token_provider)
