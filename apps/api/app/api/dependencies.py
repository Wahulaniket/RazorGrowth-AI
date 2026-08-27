"""
API dependencies.

Provides FastAPI dependency injection for authentication
and tenant scoping.
"""

from uuid import UUID

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, InvalidTokenError, TenantAccessDeniedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.tenant import Tenant
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


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Validate the user has membership for the requested tenant.

    Extracts tenant ID from X-Tenant-ID header and checks that the
    authenticated user has a TenantMembership for that tenant.

    Raises:
        ForbiddenError: If the X-Tenant-ID header is missing.
        TenantAccessDeniedError: If the user has no membership for the tenant.
    """
    if not x_tenant_id:
        raise ForbiddenError(message="X-Tenant-ID header is required.")

    try:
        tenant_uuid = UUID(x_tenant_id)
    except ValueError:
        raise ForbiddenError(message="Invalid tenant ID format.")

    # Check user's memberships (already loaded via selectin)
    for membership in current_user.memberships:
        if membership.tenant_id == tenant_uuid:
            return membership.tenant

    raise TenantAccessDeniedError()

