"""
Common Pydantic schemas for standardized API responses.

Matches the API specification's response envelope format.
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error detail in API responses."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] = Field(default_factory=dict)


class APIResponse(BaseModel):
    """Standard API response envelope.

    All API responses should use this format:
    {
        "success": true/false,
        "data": {...} or null,
        "error": {...} or null,
        "request_id": "req_..."
    }
    """

    success: bool
    data: Any = None
    error: ErrorDetail | None = None
    request_id: str | None = None
