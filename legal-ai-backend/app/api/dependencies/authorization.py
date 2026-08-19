from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user_id
from app.db.database import get_db
from app.repositories.user_permission_repository import (
    UserPermissionRepository,
)


def require_permission(permission_name: str):

    async def permission_dependency(
        user_id: int = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ) -> int:

        repository = UserPermissionRepository(db)

        has_permission = await repository.has_permission(
            user_id=user_id,
            permission_name=permission_name,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return user_id

    return permission_dependency
