from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_history import LoginHistory


class LoginHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        login_history: LoginHistory,
    ) -> LoginHistory:
        self.session.add(login_history)
        await self.session.flush()
        await self.session.refresh(login_history)

        return login_history