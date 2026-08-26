from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=255)
    default_currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )
    timezone: str = Field(default="Asia/Kolkata", max_length=100)


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    default_currency: str
    timezone: str

    model_config = ConfigDict(from_attributes=True)