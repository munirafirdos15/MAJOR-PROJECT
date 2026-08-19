import asyncio
import sys
from pathlib import Path

# Add the project root to the path so we can import app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


# Define role-permission mappings
ROLE_PERMISSIONS = {
    "User": [
        "document.view",
        "document.upload",
        "document.update",
        "document.download",
        "analysis.create",
        "analysis.view",
        "search.execute",
    ],
    "Admin": [
        "user.view",
        "user.create",
        "user.update",
        "user.delete",
        "role.view",
        "role.create",
        "role.update",
        "role.delete",
        "permission.view",
        "permission.manage",
        "document.view",
        "document.upload",
        "document.update",
        "document.delete",
        "document.download",
        "analysis.create",
        "analysis.view",
        "search.execute",
        "admin.access",
    ],
}

# Define permissions with their modules
PERMISSIONS = {
    "user.view": {"module": "user", "description": "View user details"},
    "user.create": {"module": "user", "description": "Create a new user"},
    "user.update": {"module": "user", "description": "Update user details"},
    "user.delete": {"module": "user", "description": "Delete a user"},
    "role.view": {"module": "role", "description": "View roles"},
    "role.create": {"module": "role", "description": "Create roles"},
    "role.update": {"module": "role", "description": "Update roles"},
    "role.delete": {"module": "role", "description": "Delete roles"},
    "permission.view": {"module": "permission", "description": "View permissions"},
    "permission.manage": {"module": "permission", "description": "Manage permissions"},
    "document.view": {"module": "document", "description": "View documents"},
    "document.upload": {"module": "document", "description": "Upload documents"},
    "document.update": {"module": "document", "description": "Update documents"},
    "document.delete": {"module": "document", "description": "Delete documents"},
    "document.download": {"module": "document", "description": "Download documents"},
    "analysis.create": {"module": "analysis", "description": "Create analyses"},
    "analysis.view": {"module": "analysis", "description": "View analyses"},
    "search.execute": {"module": "search", "description": "Execute searches"},
    "admin.access": {"module": "admin", "description": "Access administrative features"},
}

# Define roles with their descriptions
ROLES = {
    "User": "Standard user with basic access",
    "Admin": "Administrator with full access",
}


async def seed_permissions(session) -> dict[str, Permission]:
    """Seed permissions into the database."""
    permissions = {}

    for permission_name, permission_info in PERMISSIONS.items():
        # Check if permission already exists
        result = await session.execute(
            select(Permission).where(Permission.name == permission_name)
        )
        permission = result.scalar_one_or_none()

        if permission is None:
            permission = Permission(
                name=permission_name,
                module=permission_info["module"],
                description=permission_info["description"],
            )
            session.add(permission)
            print(f"Created permission: {permission_name}")
        else:
            print(f"Permission already exists: {permission_name}")

        permissions[permission_name] = permission

    return permissions


async def seed_roles(session) -> dict[str, Role]:
    """Seed roles into the database."""
    roles = {}

    for role_name, role_description in ROLES.items():
        # Check if role already exists
        result = await session.execute(
            select(Role).where(Role.name == role_name)
        )
        role = result.scalar_one_or_none()

        if role is None:
            role = Role(
                name=role_name,
                description=role_description,
            )
            session.add(role)
            print(f"Created role: {role_name}")
        else:
            print(f"Role already exists: {role_name}")

        roles[role_name] = role

    return roles


async def seed_role_permissions(
    session,
    roles: dict[str, Role],
    permissions: dict[str, Permission],
) -> None:
    """Seed role-permission associations into the database."""
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = roles[role_name]

        for permission_name in permission_names:
            permission = permissions[permission_name]

            # Check if role-permission association already exists
            result = await session.execute(
                select(RolePermission).where(
                    (RolePermission.role_id == role.id)
                    & (RolePermission.permission_id == permission.id)
                )
            )
            role_permission = result.scalar_one_or_none()

            if role_permission is None:
                role_permission = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                session.add(role_permission)
                print(f"Granted {permission_name} to {role_name}")
            else:
                print(
                    f"Permission already granted: "
                    f"{permission_name} → {role_name}"
                )


async def seed_authorization() -> None:
    """Main seed authorization function."""
    async with AsyncSessionLocal() as session:
        try:
            permissions = await seed_permissions(session)
            roles = await seed_roles(session)
            await seed_role_permissions(session, roles, permissions)

            await session.commit()

            print()
            print("Authorization seed completed successfully.")

        except Exception as e:
            await session.rollback()
            print("Authorization seed failed. Transaction rolled back.")
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_authorization())
