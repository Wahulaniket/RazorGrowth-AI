from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=255)


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    is_revoked: bool

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(ApiKeyResponse):
    """
    Response returned ONLY upon creation, containing the raw secret key.
    """
    secret_key: str
