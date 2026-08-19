from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        refresh_token: RefreshToken,
    ) -> RefreshToken:
        self.session.add(refresh_token)

        await self.session.flush()

        await self.session.refresh(
            refresh_token
        )

        return refresh_token

    async def get_valid_token(
        self,
        token_hash: str,
    ) -> RefreshToken | None:

        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at
                > datetime.now(timezone.utc),
            )
        )

        return result.scalar_one_or_none()

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:

        result = await self.session.execute(
            select(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at
                > datetime.now(timezone.utc),
            )
        )

        return result.scalar_one_or_none()

    async def revoke(
        self,
        refresh_token: RefreshToken,
    ) -> None:

        refresh_token.revoked_at = (
            datetime.now(timezone.utc)
        )

        await self.session.flush()