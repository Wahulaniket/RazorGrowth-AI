"""
AI-Readable Catalog Pydantic schemas.
These schemas expose only AI-approved product fields and abstract away database internals.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIVariantResponse(BaseModel):
    """AI-readable product variant representation."""
    
    id: UUID
    sku: str
    name: str
    price: Decimal
    currency: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class AIRelationshipResponse(BaseModel):
    """AI-readable product relationship representation."""
    
    target_product_id: UUID
    relationship_type: str
    score: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class AIAvailabilityResponse(BaseModel):
    """AI-readable availability representation."""
    
    product_id: UUID
    variant_id: UUID | None = None
    available_quantity: int
    reserved_quantity: int
    in_stock: bool


class AIProductResponse(BaseModel):
    """AI-readable core product representation."""
    
    id: UUID
    sku: str
    name: str
    description: str | None = None
    category: str | None = None # We will map category slug here
    brand: str | None = None
    price: Decimal
    currency: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    
    # We embed variants directly if they exist
    variants: list[AIVariantResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class AICatalogSearchRequest(BaseModel):
    """Request body for AI catalog search."""
    
    query: str | None = Field(default=None, description="Natural language search term")
    category: str | None = Field(default=None, description="Category slug to filter by")
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    in_stock_only: bool = Field(default=False)
    attributes: dict[str, str] = Field(default_factory=dict, description="Key-value pairs for exact match filtering")
    
    limit: int = Field(default=10, ge=1, le=50, description="Safe maximum limit to prevent unbounded retrieval")
    offset: int = Field(default=0, ge=0)


class AICatalogSearchResponse(BaseModel):
    """Paginated search response for AI."""
    
    items: list[AIProductResponse]
    total: int
    limit: int
    offset: int
