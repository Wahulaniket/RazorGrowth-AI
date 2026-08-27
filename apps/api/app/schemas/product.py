"""
Product Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Request body for creating a product."""

    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category_id: UUID
    brand: str | None = Field(default=None, max_length=255)
    base_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    """Request body for updating a product. All fields optional."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category_id: UUID | None = None
    brand: str | None = Field(default=None, max_length=255)
    base_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: str | None = Field(default=None, max_length=50)
    metadata: dict[str, Any] | None = None


class ProductResponse(BaseModel):
    """Public product representation."""

    id: UUID
    tenant_id: UUID
    category_id: UUID
    category_name: str | None = None
    sku: str
    name: str
    slug: str
    description: str | None = None
    status: str
    brand: str | None = None
    base_price: Decimal
    currency: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Paginated product list."""

    items: list[ProductResponse]
    total: int
    limit: int
    offset: int


class ProductSearchRequest(BaseModel):
    """Request body for POST /products/search."""

    query: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
