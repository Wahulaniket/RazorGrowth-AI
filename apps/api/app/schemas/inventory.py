"""
Inventory Pydantic schemas.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryUpdate(BaseModel):
    """Request body for updating inventory."""

    available_quantity: int = Field(ge=0)
    reserved_quantity: int = Field(default=0, ge=0)


class InventoryResponse(BaseModel):
    """Public inventory representation."""

    product_id: UUID
    variant_id: UUID | None = None
    available_quantity: int
    reserved_quantity: int
    in_stock: bool

    model_config = ConfigDict(from_attributes=True)
