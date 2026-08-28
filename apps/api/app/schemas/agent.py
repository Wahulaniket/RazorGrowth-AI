"""
Agent API Schemas.

Request and response models for the AI shopping agent endpoint.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request body for the agent chat endpoint."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language shopping request",
    )


class AgentRecommendation(BaseModel):
    """A single product recommendation."""
    product_id: str
    name: str | None = None
    price: float | None = None
    currency: str | None = None
    reasons: list[str] = Field(default_factory=list)


class AgentChatResponse(BaseModel):
    """Response from the agent chat endpoint."""
    message: str
    recommendations: list[AgentRecommendation] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    tools_used: list[str] = Field(default_factory=list)
    unavailable_info: list[str] = Field(default_factory=list)
    iteration_count: int = 0
    tool_call_count: int = 0
    total_latency_ms: float = 0.0
    model_latency_ms: float = 0.0
    tool_latency_ms: float = 0.0
