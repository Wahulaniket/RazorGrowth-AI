"""
Cart API routes.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_tenant, get_current_user, get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CartItemResponse,
    CartValidationResult,
    CartMutationConfirmation,
)
from app.services.cart_service import CartConfirmationRequired, CartError, CartService

router = APIRouter(tags=["cart"])


def _build_cart_response(cart) -> CartResponse:
    items = []
    cart_total = 0
    for item in cart.items:
        line_total = item.unit_price_snapshot * item.quantity
        cart_total += line_total
        items.append(
            CartItemResponse(
                id=item.id,
                cart_id=item.cart_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price_snapshot=item.unit_price_snapshot,
                currency=item.currency,
                line_total=line_total,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
        )
    return CartResponse(
        id=cart.id,
        tenant_id=cart.tenant_id,
        user_id=cart.user_id,
        status=cart.status,
        currency=cart.currency,
        items=items,
        cart_total=cart_total,
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
) -> Any:
    cart = await CartService.get_or_create_cart(db, tenant.id, current_user.id)
    return _build_cart_response(cart)


@router.post("/items", response_model=CartResponse)
async def add_cart_item(
    item_in: CartItemCreate,
    confirmation_token: str | None = None,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        await CartService.add_item(db, tenant.id, current_user.id, item_in, confirmation_token)
        await db.commit()
    except CartConfirmationRequired as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.confirmation.model_dump(mode="json")
        )
    except CartError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    cart = await CartService.get_or_create_cart(db, tenant.id, current_user.id)
    return _build_cart_response(cart)


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: uuid.UUID,
    item_in: CartItemUpdate,
    confirmation_token: str | None = None,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        await CartService.update_item(db, tenant.id, current_user.id, item_id, item_in, confirmation_token)
        await db.commit()
    except CartConfirmationRequired as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.confirmation.model_dump(mode="json")
        )
    except CartError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    cart = await CartService.get_or_create_cart(db, tenant.id, current_user.id)
    return _build_cart_response(cart)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: uuid.UUID,
    confirmation_token: str | None = None,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        await CartService.remove_item(db, tenant.id, current_user.id, item_id, confirmation_token)
        await db.commit()
    except CartConfirmationRequired as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.confirmation.model_dump(mode="json")
        )
    except CartError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    cart = await CartService.get_or_create_cart(db, tenant.id, current_user.id)
    return _build_cart_response(cart)


@router.delete("/", response_model=CartResponse)
async def clear_cart(
    confirmation_token: str | None = None,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
) -> Any:
    try:
        await CartService.clear_cart(db, tenant.id, current_user.id, confirmation_token)
        await db.commit()
    except CartConfirmationRequired as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=e.confirmation.model_dump(mode="json")
        )
    except CartError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    cart = await CartService.get_or_create_cart(db, tenant.id, current_user.id)
    return _build_cart_response(cart)


@router.get("/validate", response_model=CartValidationResult)
async def validate_cart(
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
) -> Any:
    return await CartService.validate_cart(db, tenant.id, current_user.id)
