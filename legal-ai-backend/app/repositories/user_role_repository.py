from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
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

    async def get_roles_for_user(
        self,
        user_id: int,
    ) -> list[Role]:
        result = await self.session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                Role.is_active.is_(True),
                Role.is_deleted.is_(False),
            )
        )

        return result.scalars().all()
