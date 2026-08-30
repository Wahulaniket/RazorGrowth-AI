import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission, get_current_tenant, get_current_user
from app.core.permissions import PermissionEnum
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.payment import PaymentResponse, PaymentCreate
from app.services.payment_service import PaymentService

router = APIRouter(prefix="", tags=["payments"])

@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def create_payment(
    request: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionEnum.CHECKOUT_WRITE)),
):
    payment = await PaymentService.create_payment_for_order(db, tenant.id, request.order_id)
    await db.commit()
    return payment

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionEnum.CHECKOUT_READ)),
):
    payment = await PaymentService.get_payment(db, tenant.id, payment_id)
    return payment
