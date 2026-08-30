"""
Agent API Routes.

Provides the POST /agent/chat endpoint for AI shopping agent interaction.
Secured with JWT/API-key authentication, tenant resolution, and RBAC.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import FakeLLMProvider, LLMProvider, create_llm_provider
from app.agents.orchestrator import run_shopping_agent
from app.agents.tools import create_catalog_tool_registry
from app.api.dependencies import get_api_key_tenant, get_current_tenant, get_current_user, require_permission
from app.core.config import get_settings
from app.core.permissions import PermissionEnum
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentRecommendation,
)


router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)


def _get_llm_provider() -> LLMProvider:
    """Build the LLM provider from application settings."""
    settings = get_settings()
    return create_llm_provider(
        provider_name=settings.llm_provider,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    dependencies=[Depends(require_permission(PermissionEnum.AGENT_USE))],
)
async def agent_chat(
    body: AgentChatRequest,
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI Shopping Agent — Discovery & Recommendation.

    Accepts a natural-language shopping request, searches the catalog using
    registered tools, and returns a grounded product recommendation.

    Authentication: JWT Bearer token.
    Tenant: Resolved from X-Tenant-ID header + membership check.
    """
    request_id = getattr(request.state, "request_id", None)

    llm = _get_llm_provider()

    registry = create_catalog_tool_registry()

    result = await run_shopping_agent(
        db=db,
        tenant_id=tenant.id,
        user_message=body.message,
        llm=llm,
        registry=registry,
        user_id=current_user.id,
        request_id=request_id,
        session_id_str=body.session_id,
    )

    # Map recommendations to the response schema
    recommendations = []
    for rec in result.recommendations:
        recommendations.append(AgentRecommendation(
            product_id=rec.get("product_id", ""),
            name=rec.get("name"),
            price=rec.get("price"),
            currency=rec.get("currency"),
            reasons=rec.get("reasons", []),
        ))

    return AgentChatResponse(
        session_id=result.session_id,
        message=result.message,
        recommendations=recommendations,
        constraints=result.constraints,
        tools_used=result.tools_used,
        unavailable_info=result.unavailable_info,
        iteration_count=result.iteration_count,
        tool_call_count=result.tool_call_count,
        total_latency_ms=result.total_latency_ms,
        model_latency_ms=result.model_latency_ms,
        tool_latency_ms=result.tool_latency_ms,
    )


@router.post(
    "/chat/apikey",
    response_model=AgentChatResponse,
    dependencies=[Depends(require_permission(PermissionEnum.AGENT_USE))],
)
async def agent_chat_apikey(
    body: AgentChatRequest,
    request: Request,
    tenant: Tenant = Depends(get_api_key_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    AI Shopping Agent — API Key authentication variant.

    Same as /agent/chat but uses X-API-Key for authentication.
    Tenant is resolved from the API key's associated tenant.
    """
    request_id = getattr(request.state, "request_id", None)

    llm = _get_llm_provider()
    registry = create_catalog_tool_registry()

    result = await run_shopping_agent(
        db=db,
        tenant_id=tenant.id,
        user_message=body.message,
        llm=llm,
        registry=registry,
        user_id=None,  # API key auth — no user
        request_id=request_id,
        session_id_str=body.session_id,
    )

    recommendations = []
    for rec in result.recommendations:
        recommendations.append(AgentRecommendation(
            product_id=rec.get("product_id", ""),
            name=rec.get("name"),
            price=rec.get("price"),
            currency=rec.get("currency"),
            reasons=rec.get("reasons", []),
        ))

    return AgentChatResponse(
        session_id=result.session_id,
        message=result.message,
        recommendations=recommendations,
        constraints=result.constraints,
        tools_used=result.tools_used,
        unavailable_info=result.unavailable_info,
        iteration_count=result.iteration_count,
        tool_call_count=result.tool_call_count,
        total_latency_ms=result.total_latency_ms,
        model_latency_ms=result.model_latency_ms,
        tool_latency_ms=result.tool_latency_ms,
    )
