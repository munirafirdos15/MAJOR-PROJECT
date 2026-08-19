from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies.auth import get_current_user_id
from app.db.database import get_db
from app.schemas.auth import (
    CurrentUserResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResendVerificationRequest,
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: UserRegistrationRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuthService(db)

        return await service.register_user(
            request
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/login",
    response_model=UserLoginResponse,
)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuthService(db)

        return await service.login_user(
            request
        )

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(ex),
        )


@router.get(
    "/verify-email",
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuthService(db)

        await service.verify_email(token)

        return {
            "message": "Email verified successfully"
        }

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/resend-verification",
)
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuthService(db)

        await service.resend_verification_email(
            request.email
        )

        return {
            "message": (
                "Verification email sent successfully"
            )
        }

    except ValueError as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ex),
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuthService(db)

        return await service.refresh_access_token(
            request.refresh_token
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = AuthService(db)

        await service.logout(
            refresh_token=request.refresh_token,
            session_id=request.session_id,
        )

        return {
            "message": "Logged out successfully"
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)

    user = await service.user_repository.get_by_id(
        user_id
    )

    if user is None or user.is_deleted or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not available",
        )

    roles = await service.user_role_repository.get_roles_for_user(
        user.id
    )

    return CurrentUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        email_verified=user.email_verified,
        roles=[role.name for role in roles],
    )
