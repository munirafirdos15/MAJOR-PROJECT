from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification_token import EmailVerificationToken


class EmailVerificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_valid_token(
        self,
        token_hash: str,
    ) -> EmailVerificationToken | None:

        result = await self.session.execute(
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.verified_at.is_(None),
                EmailVerificationToken.expires_at
                > datetime.now(timezone.utc),
            )
        )

        return result.scalar_one_or_none()

    async def mark_verified(
        self,
        verification_token: EmailVerificationToken,
    ) -> EmailVerificationToken:

        verification_token.verified_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(verification_token)

        return verification_token

    async def get_latest_for_user(
        self,
        user_id: int,
    ) -> EmailVerificationToken | None:

        result = await self.session.execute(
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.verified_at.is_(None),
            )
            .order_by(
                EmailVerificationToken.created_at.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()