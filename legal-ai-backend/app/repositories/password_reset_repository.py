from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_valid_token(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:

        result = await self.session.execute(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at
                > datetime.now(timezone.utc),
            )
        )

        return result.scalar_one_or_none()