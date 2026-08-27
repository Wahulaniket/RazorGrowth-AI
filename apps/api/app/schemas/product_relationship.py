"""
ProductRelationship Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RelationshipType = Literal[
    "ACCESSORY",
    "COMPATIBLE",
    "CROSS_SELL",
    "UPSELL",
    "ALTERNATIVE",
    "BUNDLE_ITEM",
    "REPLACEMENT",
]


class RelationshipCreate(BaseModel):
    """Request body for creating a product relationship."""

    target_product_id: UUID
    relationship_type: RelationshipType
    score: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    """Public relationship representation."""

    id: UUID
    source_product_id: UUID
    target_product_id: UUID
    target_product_name: str | None = None
    relationship_type: str
    score: Decimal
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
