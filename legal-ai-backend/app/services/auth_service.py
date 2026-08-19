import hashlib
from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.security import (
    generate_verification_token,
    hash_password,
    hash_verification_token,
    verify_password,
)
from app.models.email_verification_token import EmailVerificationToken
from app.models.login_history import LoginHistory
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.login_history_repository import (
    LoginHistoryRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_role_repository import UserRoleRepository
from app.repositories.user_session_repository import (
    UserSessionRepository,
)
from app.schemas.auth import (
    RefreshTokenRequest,
    RefreshTokenResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
)
from app.services.email_service import EmailService


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.user_repository = UserRepository(
            session
        )

        self.role_repository = RoleRepository(
            session
        )

        self.user_role_repository = (
            UserRoleRepository(session)
        )

        self.email_verification_repository = (
            EmailVerificationRepository(session)
        )

        self.refresh_token_repository = (
            RefreshTokenRepository(session)
        )

        self.user_session_repository = (
            UserSessionRepository(session)
        )

        self.login_history_repository = (
            LoginHistoryRepository(session)
        )

        self.password_reset_token_repository = (
            PasswordResetTokenRepository(session)
        )

        self.email_service = EmailService()

    # =========================================================
    # REGISTER
    # =========================================================

    async def register_user(
        self,
        request: UserRegistrationRequest,
    ) -> UserRegistrationResponse:

        existing_user = (
            await self.user_repository.get_by_username(
                request.username
            )
        )

        if existing_user:
            raise ValueError(
                "Username already exists"
            )

        existing_user = (
            await self.user_repository.get_by_email(
                request.email
            )
        )

        if existing_user:
            raise ValueError(
                "Email already registered"
            )

        role = await self.role_repository.get_by_name(
            "User"
        )

        if role is None:
            raise ValueError(
                "Default User role is not configured"
            )

        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(
                request.password
            ),
            first_name=request.first_name,
            last_name=request.last_name,
            mobile_number=request.mobile_number,
        )

        user = await self.user_repository.create(
            user
        )

        await self.user_role_repository.assign_role(
            user_id=user.id,
            role_id=role.id,
        )

        verification_token, token_hash = (
            generate_verification_token()
        )

        verification_record = (
            EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(hours=24)
                ),
            )
        )

        self.session.add(
            verification_record
        )

        await self.session.commit()

        await self.email_service.send_email_verification(
            recipient_email=user.email,
            recipient_name=user.first_name,
            verification_token=verification_token,
        )

        return UserRegistrationResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            email_verified=user.email_verified,
        )

    # =========================================================
    # VERIFY EMAIL
    # =========================================================

    async def verify_email(
        self,
        token: str,
    ) -> None:

        token_hash = hash_verification_token(
            token
        )

        verification_token = (
            await self.email_verification_repository
            .get_valid_token(token_hash)
        )

        if verification_token is None:
            raise ValueError(
                "Invalid or expired verification token"
            )

        user = await self.user_repository.get_by_id(
            verification_token.user_id
        )

        if user is None:
            raise ValueError(
                "User not found"
            )

        user.email_verified = True

        verification_token.verified_at = (
            datetime.now(timezone.utc)
        )

        await self.session.commit()

    # =========================================================
    # RESEND EMAIL VERIFICATION
    # =========================================================

    async def resend_verification_email(
        self,
        email: str,
    ) -> None:

        user = await self.user_repository.get_by_email(
            email
        )

        if user is None:
            raise ValueError(
                "Unable to process verification request"
            )

        if user.email_verified:
            raise ValueError(
                "Email is already verified"
            )

        verification_token, token_hash = (
            generate_verification_token()
        )

        verification_record = (
            EmailVerificationToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(hours=24)
                ),
            )
        )

        self.session.add(
            verification_record
        )

        await self.session.commit()

        await self.email_service.send_email_verification(
            recipient_email=user.email,
            recipient_name=user.first_name,
            verification_token=verification_token,
        )

    # =========================================================
    # LOGIN
    # =========================================================

    async def login_user(
        self,
        request: UserLoginRequest,
    ) -> UserLoginResponse:

        user = await self.user_repository.get_by_username(
            request.username
        )

        now = datetime.now(timezone.utc)

        if user is None:
            raise ValueError(
                "Invalid username or password"
            )

        # -----------------------------------------------------
        # Check account lock
        # -----------------------------------------------------

        if user.is_locked:

            if (
                user.locked_until is not None
                and user.locked_until <= now
            ):
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0

                await self.session.flush()

            else:
                raise ValueError(
                    "Account is temporarily locked"
                )

        # -----------------------------------------------------
        # Verify password
        # -----------------------------------------------------

        if not verify_password(
            request.password,
            user.password_hash,
        ):

            user.failed_login_attempts += 1

            login_history = LoginHistory(
                user_id=user.id,
                login_at=now,
                is_successful=False,
                failure_reason=(
                    "Invalid username or password"
                ),
            )

            await self.login_history_repository.create(
                login_history
            )

            # Lock account after maximum attempts
            if (
                user.failed_login_attempts
                >= settings.max_failed_login_attempts
            ):
                user.is_locked = True

                user.locked_until = (
                    now
                    + timedelta(
                        minutes=settings.account_lockout_minutes
                    )
                )

            await self.session.commit()

            raise ValueError(
                "Invalid username or password"
            )

        # -----------------------------------------------------
        # Email verification check
        # -----------------------------------------------------

        if not user.email_verified:
            raise ValueError(
                "Email address is not verified"
            )

        # -----------------------------------------------------
        # Reset failed login state
        # -----------------------------------------------------

        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None

        # -----------------------------------------------------
        # Get user roles
        # -----------------------------------------------------

        roles = await self.role_repository.get_by_user_id(
            user.id
        )

        role_names = [
            role.name
            for role in roles
        ]

        # -----------------------------------------------------
        # Create access token
        # -----------------------------------------------------

        access_token = create_access_token(
            user_id=user.id,
            roles=role_names,
        )

        # -----------------------------------------------------
        # Create refresh token
        # -----------------------------------------------------

        refresh_token = create_refresh_token(
            user_id=user.id
        )

        refresh_token_hash = (
            hash_verification_token(
                refresh_token
            )
        )

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=(
                now
                + timedelta(
                    days=settings
                    .jwt_refresh_token_expire_days
                )
            ),
        )

        await self.refresh_token_repository.create(
            refresh_record
        )

        # -----------------------------------------------------
        # Create user session
        # -----------------------------------------------------

        session_id = secrets.token_urlsafe(
            32
        )

        user_session = UserSession(
            user_id=user.id,
            refresh_token_id=refresh_record.id,
            session_id=session_id,
            last_activity_at=now,
            expires_at=(
                now
                + timedelta(
                    days=settings
                    .jwt_refresh_token_expire_days
                )
            ),
        )

        await self.user_session_repository.create(
            user_session
        )

        # -----------------------------------------------------
        # Login history
        # -----------------------------------------------------

        login_history = LoginHistory(
            user_id=user.id,
            login_at=now,
            is_successful=True,
        )

        await self.login_history_repository.create(
            login_history
        )

        await self.session.commit()

        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=(
                settings
                .jwt_access_token_expire_minutes
                * 60
            ),
        )

    # =========================================================
    # REFRESH ACCESS TOKEN
    # =========================================================

    async def refresh_access_token(
        self,
        request: RefreshTokenRequest,
    ) -> RefreshTokenResponse:

        try:
            payload = decode_token(
                request.refresh_token
            )

        except Exception:
            raise ValueError(
                "Invalid or expired refresh token"
            )

        if payload.get("type") != "refresh":
            raise ValueError(
                "Invalid refresh token"
            )

        user_id = payload.get("sub")

        if not user_id:
            raise ValueError(
                "Invalid refresh token"
            )

        try:
            user_id = int(user_id)

        except (TypeError, ValueError):
            raise ValueError(
                "Invalid refresh token"
            )

        token_hash = hash_verification_token(
            request.refresh_token
        )

        stored_token = (
            await self.refresh_token_repository
            .get_valid_token(token_hash)
        )

        if stored_token is None:
            raise ValueError(
                "Refresh token is revoked or expired"
            )

        if stored_token.user_id != user_id:
            raise ValueError(
                "Invalid refresh token"
            )

        user = await self.user_repository.get_by_id(
            user_id
        )

        if user is None:
            raise ValueError(
                "User not found"
            )

        if user.is_locked:
            raise ValueError(
                "Account is temporarily locked"
            )

        # -----------------------------------------------------
        # Get roles
        # -----------------------------------------------------

        roles = await self.role_repository.get_by_user_id(
            user.id
        )

        role_names = [
            role.name
            for role in roles
        ]

        # -----------------------------------------------------
        # Create new access token
        # -----------------------------------------------------

        new_access_token = create_access_token(
            user_id=user.id,
            roles=role_names,
        )

        # -----------------------------------------------------
        # Rotate refresh token
        # -----------------------------------------------------

        new_refresh_token = create_refresh_token(
            user_id=user.id
        )

        new_refresh_hash = (
            hash_verification_token(
                new_refresh_token
            )
        )

        now = datetime.now(timezone.utc)

        new_refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=(
                now
                + timedelta(
                    days=settings
                    .jwt_refresh_token_expire_days
                )
            ),
        )

        await self.refresh_token_repository.create(
            new_refresh_record
        )

        # Revoke old token
        stored_token.revoked_at = now

        stored_token.replaced_by_token_id = (
            new_refresh_record.id
        )

        # -----------------------------------------------------
        # Update session
        # -----------------------------------------------------

        user_session = (
            await self.user_session_repository
            .get_by_refresh_token_id(
                stored_token.id
            )
        )

        if user_session is not None:

            user_session.refresh_token_id = (
                new_refresh_record.id
            )

            user_session.last_activity_at = now

            user_session.expires_at = (
                now
                + timedelta(
                    days=settings
                    .jwt_refresh_token_expire_days
                )
            )

        await self.session.commit()

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=(
                settings
                .jwt_access_token_expire_minutes
                * 60
            ),
        )

    # =========================================================
    # LOGOUT
    # =========================================================

    async def logout(
        self,
        refresh_token: str,
        session_id: str,
    ) -> None:

        token_hash = hashlib.sha256(
            refresh_token.encode("utf-8")
        ).hexdigest()

        token = await self.refresh_token_repository.get_by_hash(
            token_hash
        )      
        if token is None:
            raise ValueError("Invalid session")
        if token.user_id is None:
            raise ValueError("Invalid session")
        user_session = (
            await self.user_session_repository
            .get_by_session_id(
                session_id
            )
        )
        if user_session is None:
            raise ValueError("Invalid session")
        if user_session.user_id != token.user_id:
            raise ValueError("Invalid session")

        await self.refresh_token_repository.revoke(token)

        await self.user_session_repository.revoke(
            user_session
        )

        await self.session.commit()

        
    # =========================================================
    # FORGOT PASSWORD
    # =========================================================

    async def forgot_password(
        self,
        email: str,
    ) -> None:

        user = await self.user_repository.get_by_email(
            email
        )

        # Security:
        # Do not reveal whether an email exists.
        if user is None:
            return

        reset_token, token_hash = (
            generate_verification_token()
        )

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ),
        )

        await self.password_reset_token_repository.create(
            reset_record
        )

        await self.session.commit()

        await self.email_service.send_password_reset_email(
            recipient_email=user.email,
            recipient_name=user.first_name,
            reset_token=reset_token,
        )

    # =========================================================
    # RESET PASSWORD
    # =========================================================

    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> None:

        token_hash = hash_verification_token(
            token
        )

        reset_token = (
            await self.password_reset_token_repository
            .get_valid_token(token_hash)
        )

        if reset_token is None:
            raise ValueError(
                "Invalid or expired password reset token"
            )

        user = await self.user_repository.get_by_id(
            reset_token.user_id
        )

        if user is None:
            raise ValueError(
                "User not found"
            )

        # Change password
        user.password_hash = hash_password(
            new_password
        )

        # Mark reset token as used
        reset_token.used_at = (
            datetime.now(timezone.utc)
        )

        # Reset account lockout state
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None

        await self.session.commit()