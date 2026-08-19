from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.username == username
            )
        )

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        user: User,
    ) -> User:
        self.session.add(user)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def update_login_failure(
        self,
        user: User,
        max_failed_attempts: int,
        lockout_minutes: int,
    ) -> User:
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= max_failed_attempts:
            user.is_locked = True

            user.locked_until = (
                datetime.now(timezone.utc)
                + timedelta(minutes=lockout_minutes)
            )

        await self.session.flush()

        return user

    async def reset_login_failures(
        self,
        user: User,
    ) -> User:
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None

        await self.session.flush()

        return user