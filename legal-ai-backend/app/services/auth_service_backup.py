from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    generate_verification_token,
    hash_password,
    hash_verification_token,
)
from app.models.email_verification_token import EmailVerificationToken
from app.models.user import User
from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_role_repository import UserRoleRepository
from app.schemas.auth import (
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

        self.email_service = EmailService()

    async def register_user(
        self,
        request: UserRegistrationRequest,
    ) -> UserRegistrationResponse:

        # Check username
        existing_user = await self.user_repository.get_by_username(
            request.username
        )

        if existing_user:
            raise ValueError("Username already exists")

        # Check email
        existing_user = await self.user_repository.get_by_email(
            request.email
        )

        if existing_user:
            raise ValueError("Email already registered")

        # Get default User role
        role = await self.role_repository.get_by_name("User")

        if role is None:
            raise ValueError(
                "Default User role is not configured"
            )

        # Create user
        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            mobile_number=request.mobile_number,
        )

        user = await self.user_repository.create(user)

        # Assign default User role
        await self.user_role_repository.assign_role(
            user_id=user.id,
            role_id=role.id,
        )

        # Generate verification token
        verification_token, token_hash = (
            generate_verification_token()
        )

        # Store only the token hash in PostgreSQL
        verification_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(hours=24)
            ),
        )

        self.session.add(verification_record)

        # Commit database transaction before sending email
        await self.session.commit()

        # Send verification email
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

        # Generate a NEW verification token
        verification_token, token_hash = (
            generate_verification_token()
        )

        # Store only the hash
        verification_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(hours=24)
            ),
        )

        self.session.add(verification_record)

        # Commit before sending email
        await self.session.commit()

        # Send new verification email
        await self.email_service.send_email_verification(
            recipient_email=user.email,
            recipient_name=user.first_name,
            verification_token=verification_token,
        )