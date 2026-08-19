
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class UserPermissionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def has_permission(
        self,
        user_id: int,
        permission_name: str,
    ) -> bool:

        result = await self.session.execute(
            select(Permission.id)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.id,
            )
            .join(
                Role,
                Role.id == RolePermission.role_id,
            )
            .join(
                UserRole,
                UserRole.role_id == Role.id,
            )
            .where(
                UserRole.user_id == user_id,
                Permission.name == permission_name,
                Permission.is_active.is_(True),
                Permission.is_deleted.is_(False),
                Role.is_active.is_(True),
                Role.is_deleted.is_(False),
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None
