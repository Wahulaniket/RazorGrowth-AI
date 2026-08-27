"""
Category routes.

All routes require authentication + tenant scoping via X-Tenant-ID header.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_tenant
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category import CategoryService


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=201,
)
async def create_category(
    data: CategoryCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new category for the current tenant."""
    return await CategoryService.create(db, tenant.id, data)


@router.get(
    "",
    response_model=list[CategoryResponse],
)
async def list_categories(
    parent_id: UUID | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List categories. Pass parent_id to list subcategories."""
    return await CategoryService.list(db, tenant.id, parent_id)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def get_category(
    category_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get a single category by ID."""
    return await CategoryService.get(db, tenant.id, category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update a category."""
    return await CategoryService.update(db, tenant.id, category_id, data)
