"""
LLM Provider Abstraction.

Defines a provider-agnostic interface for LLM interaction.
The orchestrator depends only on LLMProvider, never on a concrete SDK.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes for tool calling (provider-agnostic)
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """A single tool call requested by the model."""
    id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class LLMMessage:
    """A message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None  # for role="tool" responses
    name: str | None = None  # tool name for role="tool"


@dataclass
class LLMResponse:
    """Response from a model invocation."""
    message: LLMMessage
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    finish_reason: str = "stop"


# ---------------------------------------------------------------------------
# Abstract provider interface
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    """
    Provider-agnostic LLM interface.

    The orchestrator depends ONLY on this interface.
    Concrete implementations (OpenAI, Gemini, Fake, etc.) live behind it.
    """

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        """
        Send messages to the model, providing available tools.

        Args:
            messages:    Conversation history.
            tools:       JSON-schema tool definitions the model may call.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with optional tool_calls on the assistant message.
        """
        ...


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """Concrete provider using the OpenAI Python SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set LLM_API_KEY in your environment."
            )
        # Lazy import so the openai package doesn't leak into the rest of the app
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def generate_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        start = time.monotonic()

        # Convert internal messages to OpenAI format
        oai_messages = []
        for msg in messages:
            oai_msg: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                oai_msg["content"] = msg.content
            if msg.tool_calls:
                oai_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.tool_name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                oai_msg["tool_call_id"] = msg.tool_call_id
            if msg.name:
                oai_msg["name"] = msg.name
            oai_messages.append(oai_msg)

        # Convert tool definitions to OpenAI format
        oai_tools = [
            {"type": "function", "function": t} for t in tools
        ] if tools else None

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=oai_messages,
            tools=oai_tools,
            temperature=temperature,
        )

        elapsed = (time.monotonic() - start) * 1000
        choice = response.choices[0]
        assistant_msg = choice.message

        # Parse tool calls from the response
        parsed_tool_calls = None
        if assistant_msg.tool_calls:
            parsed_tool_calls = []
            for tc in assistant_msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                parsed_tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        tool_name=tc.function.name,
                        arguments=args,
                    )
                )

        return LLMResponse(
            message=LLMMessage(
                role="assistant",
                content=assistant_msg.content,
                tool_calls=parsed_tool_calls,
            ),
            model=self._model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            latency_ms=elapsed,
            finish_reason=choice.finish_reason or "stop",
        )


# ---------------------------------------------------------------------------
# Fake provider for deterministic testing
# ---------------------------------------------------------------------------

class FakeLLMProvider(LLMProvider):
    """
    Deterministic LLM provider for testing.

    Accepts a list of pre-scripted responses that are returned in order.
    Each response is an LLMResponse (or an Exception to simulate failures).
    """

    def __init__(self, responses: list[LLMResponse | Exception] | None = None):
        self._responses: list[LLMResponse | Exception] = responses or []
        self._call_index: int = 0
        self.calls: list[dict[str, Any]] = []  # records every invocation

    def add_response(self, response: LLMResponse | Exception) -> None:
        self._responses.append(response)

    async def generate_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        self.calls.append({
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
        })

        if self._call_index >= len(self._responses):
            # Default: return a plain text response to avoid infinite loops
            return LLMResponse(
                message=LLMMessage(role="assistant", content="No more scripted responses."),
                model="fake",
                latency_ms=0.0,
            )

        resp = self._responses[self._call_index]
        self._call_index += 1

        if isinstance(resp, Exception):
            raise resp

        return resp


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm_provider(
    provider_name: str = "openai",
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> LLMProvider:
    """
    Factory that instantiates the correct LLMProvider.
    Raises clearly if a real provider is requested without credentials.
    """
    if provider_name == "fake":
        return FakeLLMProvider()
    elif provider_name == "openai":
        return OpenAIProvider(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
