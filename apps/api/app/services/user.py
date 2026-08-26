"""
User service.

Business logic for user operations.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.user import UserRepository


class UserService:

    @staticmethod
    async def get(
        db: AsyncSession,
        user_id: UUID,
    ):
        """Get a user by ID.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise NotFoundError(resource="User")
        return user
