"""
Category Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Request body for creating a category."""

    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None


class CategoryUpdate(BaseModel):
    """Request body for updating a category. All fields optional."""

    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None


class CategoryResponse(BaseModel):
    """Public category representation."""

    id: UUID
    tenant_id: UUID
    parent_id: UUID | None = None
    name: str
    slug: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
