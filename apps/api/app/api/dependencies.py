"""
API dependencies.

Provides FastAPI dependency injection for authentication
and tenant scoping.
"""

from uuid import UUID
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, InvalidTokenError, TenantAccessDeniedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    """Extract and validate the current user from the JWT token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidTokenError(
            message="Invalid authorization header format or missing."
        )

    token = credentials.credentials

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


async def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User | None:
    """Extract and validate the current user from the JWT token, if present."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        return None

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    user = await UserRepository.get_by_id(db, user_id)
    if user is None or user.status != "ACTIVE":
        return None

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
            tenant = membership.tenant

            # Inject tenant_id into the session info dictionary.
            # The SQLAlchemy event listener in session.py will pick this up
            # and automatically run SELECT set_config('app.current_tenant', ...)
            # whenever a transaction begins, ensuring bulletproof RLS context.
            db.info["tenant_id"] = str(tenant.id)

            return tenant

    raise TenantAccessDeniedError()

async def get_tenant_by_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Fetch tenant without checking user memberships (for anonymous endpoints)."""
    if not x_tenant_id:
        raise ForbiddenError(message="X-Tenant-ID header is required.")

    try:
        tenant_uuid = UUID(x_tenant_id)
    except ValueError:
        raise ForbiddenError(message="Invalid tenant ID format.")

    from sqlalchemy import select
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid))
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        raise TenantAccessDeniedError(message="Tenant not found.")
        
    db.info["tenant_id"] = str(tenant.id)
    return tenant


from typing import Callable
from app.core.permissions import PermissionEnum

def require_permission(permission: PermissionEnum) -> Callable:
    """
    Dependency factory to check if the current user has the required permission
    within the current tenant context.
    """
    async def dependency(
        current_user: User = Depends(get_current_user),
        current_tenant: Tenant = Depends(get_current_tenant),
    ) -> None:
        # get_current_tenant already validates membership, so we just find it
        membership = next(m for m in current_user.memberships if m.tenant_id == current_tenant.id)
        
        has_permission = False
        if membership.role and membership.role.permissions:
            for p in membership.role.permissions:
                if p.name == permission.value:
                    has_permission = True
                    break
                    
        if not has_permission:
            raise ForbiddenError(message=f"Missing required permission: {permission.value}")
            
    return dependency


async def get_api_key_tenant(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Authenticate an API key and return the associated tenant context.
    Uses SECURITY DEFINER function to bypass RLS safely.
    """
    from app.core.security import verify_password
    from sqlalchemy import text
    from datetime import datetime, timezone
    
    if not x_api_key:
        raise InvalidTokenError(message="X-API-Key header is required.")
        
    prefix = x_api_key[:16]
    
    # 1. Bypass RLS using SECURITY DEFINER function
    stmt = text("SELECT tenant_id, key_hash, id, is_revoked, expires_at FROM lookup_api_key_for_auth(:prefix)")
    result = await db.execute(stmt, {"prefix": prefix})
    row = result.fetchone()
    
    if not row:
        raise InvalidTokenError(message="Invalid API Key.")
        
    tenant_id, key_hash, key_id, is_revoked, expires_at = row
    
    # 2. Verify hash
    if not verify_password(x_api_key, key_hash):
        raise InvalidTokenError(message="Invalid API Key.")
        
    # 3. Check status
    if is_revoked:
        raise InvalidTokenError(message="API Key is revoked.")
        
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise InvalidTokenError(message="API Key has expired.")
        
    # 4. (Optional) update last_used_at? 
    # Skipping to keep it read-only for auth dependency.
    
    # 5. Load tenant (now that we know they have access, we establish context)
    # Note: we need to establish context to even read the tenant if tenants table is RLS'd
    # Wait, the tenant table itself is NOT RLS'd (it has its own ID, but no tenant_id column).
    from app.models.tenant import Tenant
    from sqlalchemy import select
    
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    
    if not tenant:
        raise TenantAccessDeniedError(message="Tenant not found.")
        
    # 6. Establish RLS context
    db.info["tenant_id"] = str(tenant.id)
    db.info["api_key_id"] = str(key_id) # useful for audit logs
    
    return tenant
