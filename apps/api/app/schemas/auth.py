"""
Auth-related Pydantic schemas.

Covers registration, login, and token responses.
"""

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Request body for user registration."""

    email: str = Field(min_length=5, max_length=255)
    name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Request body for user login."""

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Response body after successful authentication."""

    access_token: str
    token_type: str = "bearer"
