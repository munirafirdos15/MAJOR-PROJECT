from datetime import datetime, timedelta, timezone
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.core.security import (
    generate_verification_token,
    hash_password,
    hash_verification_token,
    verify_password,
)
from app.models.email_verification_token import EmailVerificationToken
from app.models.login_history import LoginHistory
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_session import UserSession
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.login_history_repository import (
    LoginHistoryRepository,
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
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
)
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

        self.user_repository = UserRepository(session)
        self.role_repository = RoleRepository(session)
        self.user_role_repository = UserRoleRepository(session)

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

        self.email_service = EmailService()

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
            raise ValueError("Username already exists")

        existing_user = (
            await self.user_repository.get_by_email(
                request.email
            )
        )

        if existing_user:
            raise ValueError("Email already registered")

        role = await self.role_repository.get_by_name("User")

        if role is None:
            raise ValueError(
                "Default User role is not configured"
            )

        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            mobile_number=request.mobile_number,
        )

        user = await self.user_repository.create(user)

        await self.user_role_repository.assign_role(
            user_id=user.id,
            role_id=role.id,
        )

        verification_token, token_hash = (
            generate_verification_token()
        )

        verification_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(hours=24)
            ),
        )

        self.session.add(verification_record)

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

    async def verify_email(
        self,
        token: str,
    ) -> None:

        token_hash = hash_verification_token(token)

        verification_token = (
            await self.email_verification_repository.get_valid_token(
                token_hash
            )
        )

        if verification_token is None:
            raise ValueError(
                "Invalid or expired verification token"
            )

        user = await self.user_repository.get_by_id(
            verification_token.user_id
        )

        if user is None:
            raise ValueError("User not found")

        user.email_verified = True

        verification_token.verified_at = (
            datetime.now(timezone.utc)
        )

        await self.session.commit()

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

        verification_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(hours=24)
            ),
        )

        self.session.add(verification_record)

        await self.session.commit()

        await self.email_service.send_email_verification(
            recipient_email=user.email,
            recipient_name=user.first_name,
            verification_token=verification_token,
        )

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

        if not user.email_verified:
            raise ValueError(
                "Email address is not verified"
            )

        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None

        roles = await self.role_repository.get_by_user_id(
            user.id
        )

        role_names = [
            role.name
            for role in roles
        ]

        access_token = create_access_token(
            user_id=user.id,
            roles=role_names,
        )

        refresh_token = create_refresh_token(
            user_id=user.id,
        )

        refresh_token_hash = (
            hash_verification_token(
                refresh_token
            )
        )

        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=(
                now
                + timedelta(
                    days=settings.jwt_refresh_token_expire_days
                )
            ),
        )

        await self.refresh_token_repository.create(
            refresh_token_record
        )

        session_id = secrets.token_urlsafe(32)

        user_session = UserSession(
            user_id=user.id,
            refresh_token_id=refresh_token_record.id,
            session_id=session_id,
            last_activity_at=now,
            expires_at=(
                now
                + timedelta(
                    days=settings.jwt_refresh_token_expire_days
                )
            ),
        )

        await self.user_session_repository.create(
            user_session
        )

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
                settings.jwt_access_token_expire_minutes
                * 60
            ),
        )