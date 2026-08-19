from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession


class UserSessionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        user_session: UserSession,
    ) -> UserSession:

        self.session.add(user_session)

        await self.session.flush()

        await self.session.refresh(
            user_session
        )

        return user_session

    async def get_by_session_id(
        self,
        session_id: str,
    ) -> UserSession | None:

        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.session_id == session_id,
                UserSession.revoked_at.is_(None),
            )
        )

        return result.scalar_one_or_none()

    async def get_by_refresh_token_id(
        self,
        refresh_token_id: int,
    ) -> UserSession | None:

        result = await self.session.execute(
            select(UserSession).where(
                UserSession.refresh_token_id
                == refresh_token_id
            )
        )

        return result.scalar_one_or_none()

    async def revoke(
        self,
        user_session: UserSession,
    ) -> None:

        user_session.revoked_at = (
            datetime.now(timezone.utc)
        )

        await self.session.flush()