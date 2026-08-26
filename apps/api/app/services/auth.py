"""
Authentication service.

Handles user registration, login, and JWT token management.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import UserLogin, UserRegister


class AuthService:

    @staticmethod
    async def register(
        db: AsyncSession,
        data: UserRegister,
    ) -> User:
        """Register a new user.

        Raises:
            ConflictError: If email already exists.
        """
        existing = await UserRepository.get_by_email(db, data.email)
        if existing:
            raise ConflictError(message="A user with this email already exists.")

        hashed = hash_password(data.password)

        return await UserRepository.create(
            db,
            email=data.email,
            name=data.name,
            password_hash=hashed,
        )

    @staticmethod
    async def login(
        db: AsyncSession,
        data: UserLogin,
    ) -> str:
        """Authenticate a user and return a JWT access token.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        user = await UserRepository.get_by_email(db, data.email)

        if not user:
            raise AuthenticationError(message="Invalid email or password.")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError(message="Invalid email or password.")

        if user.status != "ACTIVE":
            raise AuthenticationError(message="Account is not active.")

        token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
        )

        return token
