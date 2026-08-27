"""
ProductVariant Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VariantCreate(BaseModel):
    """Request body for creating a product variant."""

    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    attributes: dict[str, Any] = Field(default_factory=dict)


class VariantUpdate(BaseModel):
    """Request body for updating a variant. All fields optional."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    attributes: dict[str, Any] | None = None
    status: str | None = Field(default=None, max_length=50)


class VariantResponse(BaseModel):
    """Public variant representation."""

    id: UUID
    product_id: UUID
    sku: str
    name: str
    price: Decimal
    currency: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
