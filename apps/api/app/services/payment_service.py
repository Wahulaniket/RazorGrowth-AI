import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.checkout import Order
from app.models.payment import Payment
from app.services.audit import AuditService
from app.services.payment_provider import get_payment_provider

class PaymentService:
    @staticmethod
    async def create_payment_for_order(
        db: AsyncSession, tenant_id: uuid.UUID, order_id: uuid.UUID
    ) -> Payment:
        # Check order
        result = await db.execute(
            select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundError("Order not found")
        
        if order.status != "CREATED":
            raise ValidationError("Order must be in CREATED state to initialize payment")
            
        # Check if an active payment already exists
        result = await db.execute(
            select(Payment).where(
                Payment.order_id == order.id,
                Payment.status.in_(["CREATED", "PENDING"])
            )
        )
        existing_payment = result.scalar_one_or_none()
        if existing_payment:
            return existing_payment
            
        # Create payment intent
        payment = Payment(
            tenant_id=tenant_id,
            order_id=order.id,
            amount=order.total,
            currency=order.currency,
            status="CREATED"
        )
        db.add(payment)
        
        # Call the payment provider to create an order
        # Ensure we use server-authoritative amount from the Order model
        provider = get_payment_provider()
        provider_order = await provider.create_order(
            amount=float(order.total), 
            currency=order.currency, 
            receipt_id=f"receipt_{order.id.hex[:10]}"
        )
        
        payment.razorpay_order_id = provider_order.get("id")
        
        # Update order status to PENDING_PAYMENT
        order.status = "PENDING_PAYMENT"
        
        await db.flush()
        
        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            action="payment.created",
            details={"order_id": str(order.id), "amount": str(payment.amount)}
        )
        
        return payment

    @staticmethod
    async def get_payment(
        db: AsyncSession, tenant_id: uuid.UUID, payment_id: uuid.UUID
    ) -> Payment:
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id, Payment.tenant_id == tenant_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundError("Payment not found")
        return payment

