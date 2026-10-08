"""Maps domain exceptions to HTTP responses, keeping use cases HTTP-agnostic."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from auth_service.domain.exceptions import (
    InactiveUserError,
    InvalidActorTypeError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError,
)

_STATUS_BY_EXCEPTION = {
    InvalidEmailError: status.HTTP_400_BAD_REQUEST,
    InvalidActorTypeError: status.HTTP_400_BAD_REQUEST,
    WeakPasswordError: status.HTTP_400_BAD_REQUEST,
    UserAlreadyExistsError: status.HTTP_409_CONFLICT,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    InactiveUserError: status.HTTP_403_FORBIDDEN,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    TokenRevokedError: status.HTTP_401_UNAUTHORIZED,
}


def register_exception_handlers(app: FastAPI) -> None:
    for exc_type, http_status in _STATUS_BY_EXCEPTION.items():
        app.add_exception_handler(exc_type, _make_handler(http_status))


def _make_handler(http_status: int):
    async def _handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=http_status, content={"detail": str(exc)})

    return _handler
