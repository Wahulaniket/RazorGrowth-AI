from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_tenant, get_current_user, require_permission
from app.core.permissions import PermissionEnum
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.checkout import OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(PermissionEnum.CATALOG_READ)),
):
    """Get all orders for the current user."""
    orders = await OrderService.get_orders(db, tenant_id=tenant.id, user_id=user.id)
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(PermissionEnum.CATALOG_READ)),
):
    """Get a specific order for the current user."""
    order = await OrderService.get_order(db, tenant_id=tenant.id, user_id=user.id, order_id=order_id)
    return order
