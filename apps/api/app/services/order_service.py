import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import RazorGrowthError
from app.models.checkout import Order, OrderItem

class OrderError(RazorGrowthError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(
            code="ORDER_ERROR",
            message=message,
            status_code=status_code,
        )

class OrderService:
    @staticmethod
    async def get_orders(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> List[Order]:
        stmt = select(Order).where(
            Order.tenant_id == tenant_id,
            Order.customer_id == user_id
        ).order_by(Order.created_at.desc()).options(
            selectinload(Order.items)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_order(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        stmt = select(Order).where(
            Order.tenant_id == tenant_id,
            Order.customer_id == user_id,
            Order.id == order_id
        ).options(
            selectinload(Order.items)
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            raise OrderError("Order not found", status_code=404)
            
        return order
