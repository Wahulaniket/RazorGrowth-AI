from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.api.dependencies import get_current_tenant, get_current_user, require_permission
from app.core.permissions import PermissionEnum
from app.db.session import get_db
from app.models.checkout import Order
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.checkout import CheckoutConfirmRequest, CheckoutQuoteRequest, CheckoutQuoteResponse, OrderResponse
from app.services.checkout_service import CheckoutService

router = APIRouter(tags=["Checkout"])


@router.post("/quote", response_model=CheckoutQuoteResponse)
async def create_quote(
    req: CheckoutQuoteRequest,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(PermissionEnum.CATALOG_WRITE)),
):
    """
    Creates an immutable checkout quote from the user's active cart.
    Validates inventory, prices, and evaluates applicable policies.
    """
    quote = await CheckoutService.create_quote(db, tenant.id, user.id, req.cart_id)
    await db.commit()
    return quote


@router.post("/{quote_id}/confirm", response_model=OrderResponse)
async def confirm_quote(
    quote_id: UUID,
    req: CheckoutConfirmRequest,
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(PermissionEnum.CATALOG_WRITE)),
):
    """
    Confirms an active quote and converts it into a pending order.
    Re-validates the quote and applies confirmation policies.
    """
    order = await CheckoutService.confirm_quote(db, tenant.id, user.id, quote_id, req)
    
    # Eager load items for response
    stmt = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    order_full = (await db.execute(stmt)).scalar_one()
    
    await db.commit()
    return order_full
