import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import RazorGrowthError
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.checkout import CheckoutQuote, CheckoutConfirmation, Order, OrderItem
from app.schemas.checkout import CheckoutConfirmRequest
from app.services.audit import AuditService
from app.services.cart_service import CartService
from app.services.policy_engine import PolicyEngineService


class CheckoutError(RazorGrowthError):
    def __init__(self, message: str):
        super().__init__(
            code="CHECKOUT_ERROR",
            message=message,
            status_code=400,
        )


class CheckoutService:
    @staticmethod
    async def create_quote(
        db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, cart_id: uuid.UUID
    ) -> CheckoutQuote:
        # Validate cart
        cart = await CartService.get_or_create_cart(db, tenant_id, user_id)
        if cart.id != cart_id:
            raise CheckoutError("Cart ID mismatch or cart not active")
            
        if not cart.items:
            raise CheckoutError("Cart is empty")

        validation = await CartService.validate_cart(db, tenant_id, user_id)
        if not validation.valid:
            raise CheckoutError(f"Cart validation failed: {validation.issues}")

        # Check Policy Engine
        decision = await PolicyEngineService.evaluate(
            db, tenant_id, "checkout.quote", {"cart_id": str(cart_id), "user_id": str(user_id)}
        )
        if decision.decision == "DENY":
            raise CheckoutError(f"Checkout blocked by policy: {', '.join(decision.reasons)}")

        # Calculate totals
        subtotal = Decimal("0.0")
        for item in cart.items:
            subtotal += Decimal(str(item.unit_price_snapshot)) * Decimal(str(item.quantity))

        # Basic dummy logic for discount and tax (can be expanded later)
        discount_total = Decimal("0.0")
        tax_total = subtotal * Decimal("0.18")  # 18% GST for example
        total = subtotal - discount_total + tax_total

        quote = CheckoutQuote(
            tenant_id=tenant_id,
            cart_id=cart.id,
            currency=cart.currency,
            subtotal=subtotal,
            discount_total=discount_total,
            tax_total=tax_total,
            total=total,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            status="ACTIVE"
        )
        db.add(quote)
        await db.flush()

        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="checkout.quote_created",
            entity_type="checkout_quote",
            entity_id=quote.id,
            details={"total": float(total)}
        )
        return quote

    @staticmethod
    async def confirm_quote(
        db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID, quote_id: uuid.UUID, req: CheckoutConfirmRequest
    ) -> Order:
        stmt = select(CheckoutQuote).where(
            CheckoutQuote.id == quote_id, 
            CheckoutQuote.tenant_id == tenant_id,
            CheckoutQuote.status == "ACTIVE"
        )
        quote = (await db.execute(stmt)).scalar_one_or_none()
        if not quote:
            raise CheckoutError("Quote not found or inactive")

        if quote.expires_at < datetime.now(timezone.utc):
            quote.status = "EXPIRED"
            await db.flush()
            raise CheckoutError("Quote has expired")

        # Re-validate Cart
        cart = await CartService.get_or_create_cart(db, tenant_id, user_id)
        if cart.id != quote.cart_id:
            raise CheckoutError("Cart mismatch")

        validation = await CartService.validate_cart(db, tenant_id, user_id)
        if not validation.valid:
            raise CheckoutError(f"Cart validation failed: {validation.issues}")

        # Check Policy Engine
        decision = await PolicyEngineService.evaluate(
            db, tenant_id, "checkout.confirm", {
                "quote_id": str(quote.id),
                "total": float(quote.total),
                "user_id": str(user_id)
            }
        )
        if decision.decision == "DENY":
            raise CheckoutError(f"Confirmation blocked by policy: {', '.join(decision.reasons)}")

        # Create Confirmation
        confirmation = CheckoutConfirmation(
            tenant_id=tenant_id,
            checkout_quote_id=quote.id,
            session_id=req.session_id,
            confirmation_type=req.confirmation_type,
            confirmed_amount=quote.total,
            currency=quote.currency,
            metadata_=req.metadata
        )
        db.add(confirmation)

        # Create Order
        order = Order(
            tenant_id=tenant_id,
            customer_id=user_id,
            cart_id=cart.id,
            currency=quote.currency,
            subtotal=quote.subtotal,
            discount_total=quote.discount_total,
            tax_total=quote.tax_total,
            total=quote.total,
            status="CREATED",
            payment_status="UNPAID"
        )
        db.add(order)
        await db.flush()

        # Create Order Items
        # We need to eagerly load product to get product_name and sku
        stmt_cart = select(Cart).where(Cart.id == cart.id).options(selectinload(Cart.items).selectinload(CartItem.product))
        cart_full = (await db.execute(stmt_cart)).scalar_one()

        for item in cart_full.items:
            order_item = OrderItem(
                tenant_id=tenant_id,
                order_id=order.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=item.product.name,
                sku=item.product.sku,
                quantity=item.quantity,
                unit_price=item.unit_price_snapshot,
                discount_amount=Decimal("0.0"),
                line_total=Decimal(str(item.unit_price_snapshot)) * Decimal(str(item.quantity))
            )
            db.add(order_item)

        # Update Quote and Cart
        quote.status = "CONFIRMED"
        cart.status = "CONVERTED"
        await db.flush()

        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="checkout.order_created",
            entity_type="order",
            entity_id=order.id,
            details={"quote_id": str(quote.id)}
        )

        return order
