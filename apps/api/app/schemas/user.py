"""
User Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """Public user representation (never includes password_hash)."""

    id: UUID
    email: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithTenants(UserResponse):
    """User with their tenant memberships."""

    tenants: list[dict] = Field(default_factory=list)
