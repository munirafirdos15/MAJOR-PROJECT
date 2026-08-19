from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.user_role import UserRole


class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        result = await self.session.execute(
            select(Role).where(
                Role.name == name
            )
        )

        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: int,
    ) -> list[Role]:
        result = await self.session.execute(
            select(Role)
            .join(
                UserRole,
                UserRole.role_id == Role.id,
            )
            .where(
                UserRole.user_id == user_id
            )
        )

        return list(result.scalars().all())