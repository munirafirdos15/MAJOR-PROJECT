from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from app.core.security import hash_verification_token


class EmailVerificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = EmailVerificationRepository(session)

    async def verify_email(self, token: str) -> None:

        if not token:
            raise ValueError("Verification token is required")

        token_hash = hash_verification_token(token)

        verification_token = await self.repository.get_valid_token(
            token_hash
        )

        if verification_token is None:
            raise ValueError(
                "Invalid or expired verification token"
            )

        user = verification_token.user

        if user is None:
            raise ValueError(
                "User associated with verification token was not found"
            )

        if user.email_verified:
            raise ValueError(
                "Email is already verified"
            )

        user.email_verified = True

        await self.repository.mark_verified(
            verification_token
        )

        await self.session.commit()