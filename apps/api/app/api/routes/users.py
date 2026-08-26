"""
User management routes.

GET /users/me/tenants — Get tenants for the current user
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserWithTenants


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me/tenants",
    response_model=UserWithTenants,
)
async def get_my_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user and their tenant memberships."""
    # Since memberships is lazy='selectin', it's already loaded
    # and the tenant relationships inside it are also 'selectin'
    
    tenants_data = []
    for membership in current_user.memberships:
        tenants_data.append({
            "id": membership.tenant.id,
            "name": membership.tenant.name,
            "slug": membership.tenant.slug,
            "role": membership.role.name,
        })
        
    return UserWithTenants(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        status=current_user.status,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        tenants=tenants_data,
    )
