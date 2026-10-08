from fastapi import APIRouter, Depends, status

from auth_service.application.dto import (
    LoginInput,
    RefreshTokenInput,
    RegisterUserInput,
    ValidateTokenInput,
)
from auth_service.application.use_cases.login_user import LoginUserUseCase
from auth_service.application.use_cases.refresh_token import RefreshTokenUseCase
from auth_service.application.use_cases.register_user import RegisterUserUseCase
from auth_service.application.use_cases.validate_token import ValidateTokenUseCase
from auth_service.presentation.dependencies import (
    get_login_use_case,
    get_refresh_use_case,
    get_register_use_case,
    get_validate_use_case,
)
from auth_service.presentation.schemas.auth_schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    ValidateRequest,
    ValidateResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest, use_case: RegisterUserUseCase = Depends(get_register_use_case)
) -> RegisterResponse:
    result = use_case.execute(
        RegisterUserInput(email=request.email, password=request.password, actor_type=request.actor_type)
    )
    return RegisterResponse(
        id=result.id,
        email=result.email,
        is_admin=result.is_admin,
        actor_type=result.actor_type,
        created_at=result.created_at,
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(request: LoginRequest, use_case: LoginUserUseCase = Depends(get_login_use_case)) -> TokenResponse:
    result = use_case.execute(LoginInput(email=request.email, password=request.password))
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh(
    request: RefreshRequest, use_case: RefreshTokenUseCase = Depends(get_refresh_use_case)
) -> TokenResponse:
    result = use_case.execute(RefreshTokenInput(refresh_token=request.refresh_token))
    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.post("/validate", response_model=ValidateResponse, status_code=status.HTTP_200_OK)
def validate(
    request: ValidateRequest, use_case: ValidateTokenUseCase = Depends(get_validate_use_case)
) -> ValidateResponse:
    result = use_case.execute(ValidateTokenInput(token=request.token))
    return ValidateResponse(
        valid=result.valid,
        user_id=result.user_id,
        email=result.email,
        expires_at=result.expires_at,
        reason=result.reason,
        is_admin=result.is_admin,
        aud=result.aud,
        permissions=result.permissions,
    )
