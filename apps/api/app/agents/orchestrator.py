"""
Agent Orchestrator.

Implements the bounded tool-calling loop for the AI shopping agent.
The orchestrator depends on LLMProvider (not a concrete SDK) and
ToolRegistry (not direct DB access).

Security invariants:
- Tenant context comes from the authenticated session, never from the LLM.
- The agent can only call registered tools.
- The loop is strictly bounded (max 5 iterations).
- Chain-of-thought is never stored; only operational traces are recorded.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import LLMProvider, LLMMessage, LLMResponse, ToolCall
from app.agents.tools import ToolRegistry, ToolResult
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

# Strict upper bound on model/tool iterations
MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are a helpful AI shopping assistant for a merchant's product catalog.

Your ONLY job is product discovery and recommendation. You CANNOT:
- Create carts, checkout, process payments, or perform any transactions
- Access data from other merchants or tenants
- Make up product specifications, prices, availability, or any catalog facts

RULES:
1. Use the provided tools to search for products, get details, check availability, and find relationships.
2. ONLY state facts that come directly from tool results. If information is unavailable, say so explicitly.
3. Never invent prices, SKUs, availability, discounts, warranties, or shipping information.
4. Extract explicit shopping constraints from the user's request (category, budget, attributes).
5. Do NOT fabricate constraints the user didn't mention.
6. When making a recommendation, provide clear reasons grounded in catalog data.
7. Keep responses concise and helpful.

When you have enough information to make a recommendation, respond with a JSON object in this exact format:
```json
{
    "message": "Your natural language response to the user",
    "recommendations": [
        {
            "product_id": "uuid-string",
            "name": "Product Name",
            "price": 1234.56,
            "currency": "INR",
            "reasons": ["reason1", "reason2"]
        }
    ],
    "constraints": {
        "category": "extracted category or null",
        "max_price": 1234 or null,
        "min_price": 0 or null,
        "attributes": {}
    },
    "unavailable_info": ["list of information you could not confirm"]
}
```

If no products match, respond with the same JSON format but with an empty recommendations list and a helpful message.
"""


# ---------------------------------------------------------------------------
# Trace event types (operational only — no chain-of-thought)
# ---------------------------------------------------------------------------

@dataclass
class TraceEvent:
    """A single operational trace event."""
    event: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp_ms: float = 0.0


# ---------------------------------------------------------------------------
# Agent execution result
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Full result from the agent orchestrator."""
    message: str
    recommendations: list[dict[str, Any]]
    constraints: dict[str, Any]
    tools_used: list[str]
    unavailable_info: list[str]
    trace: list[TraceEvent]
    iteration_count: int
    tool_call_count: int
    total_latency_ms: float
    model_latency_ms: float
    tool_latency_ms: float
    outcome: str  # "success", "max_iterations", "error"


# ---------------------------------------------------------------------------
# Agent orchestrator
# ---------------------------------------------------------------------------

async def run_shopping_agent(
    db: AsyncSession,
    tenant_id: UUID,
    user_message: str,
    llm: LLMProvider,
    registry: ToolRegistry,
    user_id: UUID | None = None,
    request_id: str | None = None,
) -> AgentResult:
    """
    Execute the bounded shopping agent loop.

    1. Build the conversation with system prompt + user message.
    2. Send to LLM with available tools.
    3. If LLM requests tool calls, validate & execute them, append results.
    4. Repeat until the LLM produces a final response or max iterations reached.
    5. Parse the structured recommendation from the final response.
    6. Record operational trace events (no chain-of-thought).
    """
    start_total = time.monotonic()
    trace: list[TraceEvent] = []
    tools_used: list[str] = []
    tool_call_count = 0
    model_latency_total = 0.0
    tool_latency_total = 0.0

    # --- Trace: request received ---
    trace.append(TraceEvent(
        event="agent.request_received",
        data={"request_id": request_id, "message_length": len(user_message)},
        timestamp_ms=0.0,
    ))

    # Audit: request received
    try:
        await AuditService.log_event(
            db,
            action="agent.request_received",
            details={"request_id": request_id, "message_length": len(user_message)},
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type="agent_session",
        )
    except Exception:
        logger.warning("Failed to write audit log for agent.request_received")

    # Build conversation
    messages: list[LLMMessage] = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=user_message),
    ]

    tool_schemas = registry.get_openai_tool_schemas()
    outcome = "success"
    final_message = ""
    final_recommendations: list[dict[str, Any]] = []
    final_constraints: dict[str, Any] = {}
    final_unavailable: list[str] = []

    for iteration in range(MAX_ITERATIONS):
        # --- Call LLM ---
        try:
            llm_response: LLMResponse = await llm.generate_with_tools(
                messages=messages,
                tools=tool_schemas,
                temperature=0.0,
            )
        except Exception as e:
            logger.exception("LLM provider error")
            trace.append(TraceEvent(event="agent.llm_error", data={"error": str(e)}))
            outcome = "error"
            final_message = "I'm sorry, I encountered an error while processing your request. Please try again later."
            break

        model_latency_total += llm_response.latency_ms
        assistant_msg = llm_response.message

        # --- No tool calls → final response ---
        if not assistant_msg.tool_calls:
            trace.append(TraceEvent(
                event="agent.final_response",
                data={"iteration": iteration, "finish_reason": llm_response.finish_reason},
            ))

            # Parse structured response from assistant content
            parsed = _parse_agent_response(assistant_msg.content or "")
            final_message = parsed.get("message", assistant_msg.content or "")
            final_recommendations = parsed.get("recommendations", [])
            final_constraints = parsed.get("constraints", {})
            final_unavailable = parsed.get("unavailable_info", [])

            messages.append(assistant_msg)
            break

        # --- Process tool calls ---
        messages.append(assistant_msg)

        for tc in assistant_msg.tool_calls:
            tool_call_count += 1

            trace.append(TraceEvent(
                event="agent.tool_called",
                data={"tool": tc.tool_name, "iteration": iteration},
            ))

            # Execute through the registry (validates & enforces tenant isolation)
            result: ToolResult = await registry.execute(
                tool_name=tc.tool_name,
                arguments=tc.arguments,
                db=db,
                tenant_id=tenant_id,
            )

            tool_latency_total += result.latency_ms

            if result.success and tc.tool_name not in tools_used:
                tools_used.append(tc.tool_name)

            trace.append(TraceEvent(
                event="agent.tool_completed",
                data={
                    "tool": tc.tool_name,
                    "success": result.success,
                    "latency_ms": round(result.latency_ms, 2),
                },
            ))

            # Audit: tool execution
            try:
                await AuditService.log_event(
                    db,
                    action="agent.tool_called",
                    details={
                        "tool": tc.tool_name,
                        "success": result.success,
                        "request_id": request_id,
                    },
                    tenant_id=tenant_id,
                    user_id=user_id,
                    entity_type="agent_tool",
                )
            except Exception:
                logger.warning("Failed to write audit log for agent.tool_called")

            # Build tool response message
            tool_response_content = json.dumps(
                result.data if result.success else {"error": result.error},
                default=str,
            )

            messages.append(LLMMessage(
                role="tool",
                content=tool_response_content,
                tool_call_id=tc.id,
                name=tc.tool_name,
            ))
    else:
        # Loop exhausted without a final response
        outcome = "max_iterations"
        trace.append(TraceEvent(event="agent.max_iterations_reached", data={"iterations": MAX_ITERATIONS}))
        final_message = (
            "I've searched extensively but couldn't complete my analysis within "
            "the allowed number of steps. Here's what I found so far based on "
            "the catalog data."
        )

    total_latency = (time.monotonic() - start_total) * 1000

    # --- Trace: recommendation generated ---
    trace.append(TraceEvent(
        event="agent.recommendation_generated",
        data={
            "recommendation_count": len(final_recommendations),
            "tools_used": tools_used,
            "tool_call_count": tool_call_count,
            "outcome": outcome,
        },
    ))

    # Audit: completion
    try:
        await AuditService.log_event(
            db,
            action="agent.recommendation_generated",
            details={
                "request_id": request_id,
                "outcome": outcome,
                "recommendation_count": len(final_recommendations),
                "tool_call_count": tool_call_count,
                "total_latency_ms": round(total_latency, 2),
            },
            tenant_id=tenant_id,
            user_id=user_id,
            entity_type="agent_session",
        )
    except Exception:
        logger.warning("Failed to write audit log for agent.recommendation_generated")

    return AgentResult(
        message=final_message,
        recommendations=final_recommendations,
        constraints=final_constraints,
        tools_used=tools_used,
        unavailable_info=final_unavailable,
        trace=trace,
        iteration_count=min(iteration + 1, MAX_ITERATIONS) if 'iteration' in dir() else 0,
        tool_call_count=tool_call_count,
        total_latency_ms=round(total_latency, 2),
        model_latency_ms=round(model_latency_total, 2),
        tool_latency_ms=round(tool_latency_total, 2),
        outcome=outcome,
    )


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_agent_response(content: str) -> dict[str, Any]:
    """
    Parse the agent's final response, extracting structured JSON.
    Falls back to treating the entire content as a plain message.
    """
    if not content:
        return {"message": ""}

    # Try to extract JSON from markdown code block
    json_start = content.find("```json")
    if json_start != -1:
        json_start = content.index("\n", json_start) + 1
        json_end = content.find("```", json_start)
        if json_end != -1:
            try:
                return json.loads(content[json_start:json_end])
            except json.JSONDecodeError:
                pass

    # Try to parse the entire content as JSON
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "message" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    # Fallback: plain text message
    return {"message": content}
