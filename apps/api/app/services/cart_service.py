"""
Cart Service.

Handles business logic for cart mutations, price snapshotting, inventory validation,
and server-side confirmation boundaries.
"""

import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartValidationIssue,
    CartValidationResult,
    CartMutationConfirmation,
)
from app.services.audit import AuditService


class CartError(Exception):
    pass


class CartConfirmationRequired(Exception):
    def __init__(self, confirmation: CartMutationConfirmation):
        self.confirmation = confirmation
        super().__init__("Confirmation required")


class CartService:
    @staticmethod
    async def get_or_create_cart(db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Cart:
        stmt = select(Cart).where(
            Cart.tenant_id == tenant_id,
            Cart.user_id == user_id,
            Cart.status == "ACTIVE"
        ).options(selectinload(Cart.items).selectinload(CartItem.product))
        result = await db.execute(stmt)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(
                tenant_id=tenant_id,
                user_id=user_id,
                status="ACTIVE",
                currency="INR"
            )
            db.add(cart)
            await db.flush()
            await db.refresh(cart, ["items"])
            await AuditService.log_event(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action="cart.created",
                entity_type="cart",
                entity_id=str(cart.id), details={}
            )
        return cart

    @staticmethod
    def generate_confirmation_token(
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        target_id: str,
        quantity: int | None = None,
        price_snapshot: Decimal | None = None,
        variant_id: str | None = None
    ) -> str:
        data = {
            "sub": str(user_id),
            "type": "cart_confirmation",
            "tenant_id": str(tenant_id),
            "action": action,
            "target_id": target_id,
            "quantity": quantity,
            "price_snapshot": str(price_snapshot) if price_snapshot is not None else None,
            "variant_id": str(variant_id) if variant_id else None
        }
        return create_access_token(data=data, expires_delta=timedelta(minutes=15))

    @staticmethod
    def verify_confirmation_token(
        token: str,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        target_id: str,
        quantity: int | None = None,
        variant_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            payload = decode_access_token(token)
        except JWTError:
            raise CartError("Invalid or expired confirmation token")

        if payload.get("type") != "cart_confirmation":
            raise CartError("Invalid token type")
        if payload.get("sub") != str(user_id):
            raise CartError("Confirmation token belongs to a different user")
        if payload.get("tenant_id") != str(tenant_id):
            raise CartError("Confirmation token belongs to a different tenant")
        if payload.get("action") != action:
            raise CartError(f"Token action mismatch: expected {action}")
        if payload.get("target_id") != target_id:
            raise CartError("Token target mismatch")
        if quantity is not None and payload.get("quantity") != quantity:
            raise CartError("Token quantity mismatch")
        if variant_id and payload.get("variant_id") != variant_id:
            raise CartError("Token variant mismatch")

        return payload

    @staticmethod
    async def get_current_price_and_inventory(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        product_id: uuid.UUID,
        variant_id: uuid.UUID | None
    ) -> tuple[Decimal, int, str]:
        # Fetch Product
        stmt = select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
        product = (await db.execute(stmt)).scalar_one_or_none()
        if not product:
            raise CartError("Product not found")
        if product.status != "ACTIVE":
            raise CartError("Product is inactive")

        currency = product.currency
        current_price = product.base_price

        if variant_id:
            stmt = select(ProductVariant).where(
                ProductVariant.id == variant_id,
                ProductVariant.product_id == product_id,
                ProductVariant.tenant_id == tenant_id
            )
            variant = (await db.execute(stmt)).scalar_one_or_none()
            if not variant:
                raise CartError("Variant not found")
            if variant.status != "ACTIVE":
                raise CartError("Variant is inactive")
            current_price = variant.price
            currency = variant.currency

        # Fetch Inventory
        stmt = select(Inventory).where(
            Inventory.tenant_id == tenant_id,
            Inventory.product_id == product_id,
            Inventory.variant_id == variant_id
        )
        inv = (await db.execute(stmt)).scalar_one_or_none()
        effective_stock = 0
        if inv:
            effective_stock = max(0, inv.available_quantity - inv.reserved_quantity)

        return current_price, effective_stock, currency

    @classmethod
    async def add_item(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        item_data: CartItemCreate,
        confirmation_token: str | None = None
    ) -> CartItem:
        if item_data.quantity <= 0:
            raise CartError("Quantity must be greater than 0")

        current_price, effective_stock, currency = await cls.get_current_price_and_inventory(
            db, tenant_id, item_data.product_id, item_data.variant_id
        )

        if effective_stock < item_data.quantity:
            raise CartError("Insufficient inventory")

        # Confirmation Boundary
        if not confirmation_token:
            # Need confirmation
            token = cls.generate_confirmation_token(
                tenant_id=tenant_id,
                user_id=user_id,
                action="add_item",
                target_id=str(item_data.product_id),
                quantity=item_data.quantity,
                price_snapshot=current_price,
                variant_id=str(item_data.variant_id) if item_data.variant_id else None
            )
            raise CartConfirmationRequired(
                CartMutationConfirmation(
                    confirmation_token=token,
                    action="add_item",
                    message="Please confirm adding to cart",
                    current_price=current_price
                )
            )
        
        # Verify Token
        payload = cls.verify_confirmation_token(
            token=confirmation_token,
            tenant_id=tenant_id,
            user_id=user_id,
            action="add_item",
            target_id=str(item_data.product_id),
            quantity=item_data.quantity,
            variant_id=str(item_data.variant_id) if item_data.variant_id else None
        )
        
        # Verify Price hasn't changed since token generation
        token_price = Decimal(payload["price_snapshot"])
        if token_price != current_price:
            raise CartError(f"PRICE_CHANGED: Price has changed from {token_price} to {current_price}. Please request confirmation again.")

        cart = await cls.get_or_create_cart(db, tenant_id, user_id)

        # Check if item already exists
        existing_item = next(
            (i for i in cart.items if i.product_id == item_data.product_id and i.variant_id == item_data.variant_id),
            None
        )

        if existing_item:
            # Revalidate inventory for new total
            new_qty = existing_item.quantity + item_data.quantity
            if effective_stock < new_qty:
                raise CartError("Insufficient inventory for combined quantity")
            existing_item.quantity = new_qty
            existing_item.unit_price_snapshot = current_price
            item = existing_item
        else:
            item = CartItem(
                cart_id=cart.id,
                tenant_id=tenant_id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                quantity=item_data.quantity,
                unit_price_snapshot=current_price,
                currency=currency
            )
            db.add(item)
            cart.items.append(item)
        
        await db.flush()
        
        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="cart.item_added",
            entity_type="cart_item",
            entity_id=str(item.id),
            details={"product_id": str(item.product_id), "quantity": item.quantity}
        )
        return item

    @classmethod
    async def update_item(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        update_data: CartItemUpdate,
        confirmation_token: str | None = None
    ) -> CartItem:
        if update_data.quantity <= 0:
            raise CartError("Quantity must be greater than 0")

        cart = await cls.get_or_create_cart(db, tenant_id, user_id)
        
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise CartError("Cart item not found")

        current_price, effective_stock, currency = await cls.get_current_price_and_inventory(
            db, tenant_id, item.product_id, item.variant_id
        )

        if effective_stock < update_data.quantity:
            raise CartError("Insufficient inventory")

        if not confirmation_token:
            token = cls.generate_confirmation_token(
                tenant_id=tenant_id,
                user_id=user_id,
                action="update_item",
                target_id=str(item_id),
                quantity=update_data.quantity,
                price_snapshot=current_price
            )
            raise CartConfirmationRequired(
                CartMutationConfirmation(
                    confirmation_token=token,
                    action="update_item",
                    message="Please confirm updating item quantity",
                    current_price=current_price
                )
            )
        
        payload = cls.verify_confirmation_token(
            token=confirmation_token,
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_item",
            target_id=str(item_id),
            quantity=update_data.quantity
        )
        
        token_price = Decimal(payload["price_snapshot"])
        if token_price != current_price:
            raise CartError(f"PRICE_CHANGED: Price has changed from {token_price} to {current_price}. Please request confirmation again.")

        item.quantity = update_data.quantity
        item.unit_price_snapshot = current_price
        
        await db.flush()
        
        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="cart.item_updated",
            entity_type="cart_item",
            entity_id=str(item.id),
            details={"quantity": item.quantity}
        )
        return item

    @classmethod
    async def remove_item(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        confirmation_token: str | None = None
    ) -> None:
        cart = await cls.get_or_create_cart(db, tenant_id, user_id)
        
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise CartError("Cart item not found")

        if not confirmation_token:
            token = cls.generate_confirmation_token(
                tenant_id=tenant_id,
                user_id=user_id,
                action="remove_item",
                target_id=str(item_id)
            )
            raise CartConfirmationRequired(
                CartMutationConfirmation(
                    confirmation_token=token,
                    action="remove_item",
                    message="Please confirm removing item from cart"
                )
            )

        cls.verify_confirmation_token(
            token=confirmation_token,
            tenant_id=tenant_id,
            user_id=user_id,
            action="remove_item",
            target_id=str(item_id)
        )

        await db.delete(item)
        cart.items.remove(item)
        await db.flush()

        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="cart.item_removed",
            entity_type="cart_item",
            entity_id=str(item_id), details={}
        )

    @classmethod
    async def clear_cart(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        confirmation_token: str | None = None
    ) -> None:
        cart = await cls.get_or_create_cart(db, tenant_id, user_id)

        if not confirmation_token:
            token = cls.generate_confirmation_token(
                tenant_id=tenant_id,
                user_id=user_id,
                action="clear_cart",
                target_id=str(cart.id)
            )
            raise CartConfirmationRequired(
                CartMutationConfirmation(
                    confirmation_token=token,
                    action="clear_cart",
                    message="Please confirm clearing your cart"
                )
            )

        cls.verify_confirmation_token(
            token=confirmation_token,
            tenant_id=tenant_id,
            user_id=user_id,
            action="clear_cart",
            target_id=str(cart.id)
        )

        for item in list(cart.items):
            await db.delete(item)
            cart.items.remove(item)
        
        await db.flush()

        await AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            user_id=user_id,
            action="cart.cleared",
            entity_type="cart",
            entity_id=str(cart.id), details={}
        )

    @classmethod
    async def validate_cart(cls, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID) -> CartValidationResult:
        cart = await cls.get_or_create_cart(db, tenant_id, user_id)
        issues = []

        for item in cart.items:
            try:
                current_price, effective_stock, _ = await cls.get_current_price_and_inventory(
                    db, tenant_id, item.product_id, item.variant_id
                )
                if current_price != item.unit_price_snapshot:
                    issues.append(CartValidationIssue(
                        type="PRICE_CHANGED",
                        product_id=item.product_id,
                        variant_id=item.variant_id,
                        message="Price has changed since adding to cart.",
                        old_price=item.unit_price_snapshot,
                        current_price=current_price
                    ))
                if effective_stock < item.quantity:
                    issues.append(CartValidationIssue(
                        type="INSUFFICIENT_STOCK",
                        product_id=item.product_id,
                        variant_id=item.variant_id,
                        message=f"Only {effective_stock} items remaining in stock."
                    ))
            except CartError as e:
                issues.append(CartValidationIssue(
                    type="PRODUCT_INACTIVE",
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    message=str(e)
                ))
        
        if issues:
            await AuditService.log_event(
                db=db,
                tenant_id=tenant_id,
                user_id=user_id,
                action="cart.validation_failed",
                entity_type="cart",
                entity_id=str(cart.id),
                details={"issue_count": len(issues)}
            )

        return CartValidationResult(
            valid=len(issues) == 0,
            issues=issues
        )
