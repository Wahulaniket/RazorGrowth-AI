"""
API dependencies.

Provides FastAPI dependency injection for authentication
and tenant scoping.
"""

from uuid import UUID

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> User:
    """Extract and validate the current user from the JWT token.

    Expected header format: Authorization: Bearer <token>

    Raises:
        InvalidTokenError: If the token is missing, invalid, or expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidTokenError(message="Invalid authorization header format or missing.")

    token = authorization[7:]  # Strip "Bearer "

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise InvalidTokenError()

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise InvalidTokenError(message="Token missing subject claim.")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise InvalidTokenError(message="Invalid user ID in token.")

    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise InvalidTokenError(message="User not found.")

    if user.status != "ACTIVE":
        raise InvalidTokenError(message="User account is not active.")

    return user
