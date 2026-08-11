from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository

from app.schemas.auth import (
    UserRegistrationRequest,
    UserRegistrationResponse,
)

from app.core.security import hash_password


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repository = UserRepository(session)
        self.session = session

    async def register_user(
        self,
        request: UserRegistrationRequest,
    ) -> UserRegistrationResponse:

        # Check username
        existing_user = await self.user_repository.get_by_username(
            request.username
        )

        if existing_user:
            raise ValueError("Username already exists")

        # Check email
        existing_user = await self.user_repository.get_by_email(
            request.email
        )

        if existing_user:
            raise ValueError("Email already registered")

        # Create user
        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            mobile_number=request.mobile_number,
        )

        user = await self.user_repository.create(user)

        await self.session.commit()

        return UserRegistrationResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            email_verified=user.email_verified,
        )
