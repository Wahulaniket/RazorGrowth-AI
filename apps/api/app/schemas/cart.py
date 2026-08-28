"""
Cart Schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: uuid.UUID
    cart_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: int
    unit_price_snapshot: Decimal
    currency: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None
    status: str
    currency: str
    items: list[CartItemResponse]
    cart_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartValidationIssue(BaseModel):
    type: str # e.g., "PRICE_CHANGED", "INSUFFICIENT_STOCK", "PRODUCT_INACTIVE"
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    message: str
    old_price: Decimal | None = None
    current_price: Decimal | None = None


class CartValidationResult(BaseModel):
    valid: bool
    issues: list[CartValidationIssue]


# For the confirmation flow
class CartMutationConfirmation(BaseModel):
    confirmation_token: str
    action: str
    message: str
    current_price: Decimal | None = None
