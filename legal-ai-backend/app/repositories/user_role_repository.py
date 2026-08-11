from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_role import UserRole


class UserRoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def assign_role(
        self,
        user_id: int,
        role_id: int,
    ) -> UserRole:
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
        )

        self.session.add(user_role)
        await self.session.flush()

        return user_role
