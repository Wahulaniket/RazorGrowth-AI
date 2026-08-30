"""
Tool Registry.

Defines a strict, validated tool abstraction for AI agent interaction.
Each tool has a name, description, JSON-schema for inputs/outputs,
validation logic, and a handler that calls application-level services.

The LLM never receives database credentials, SQL, or tenant_id.
Tenant context comes exclusively from the authenticated session.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable, Awaitable
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.schemas.ai_catalog import (
    AICatalogSearchRequest,
)
from app.services.ai_catalog import AICatalogService
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.services.cart_service import CartService, CartConfirmationRequired, CartError

logger = logging.getLogger(__name__)

# Maximum sizes to bound tool responses sent to the model
MAX_SEARCH_RESULTS = 5
MAX_RELATIONSHIPS = 10
MAX_TOOL_INPUT_SIZE = 2048  # bytes


# ---------------------------------------------------------------------------
# Tool execution result
# ---------------------------------------------------------------------------

@dataclass
class ToolResult:
    """Result of executing a registered tool."""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Tool input schemas (what the LLM sees — NO tenant_id)
# ---------------------------------------------------------------------------

class CatalogSearchInput(BaseModel):
    """Input schema for catalog.search."""
    model_config = {"extra": "forbid"}
    query: str | None = Field(default=None, description="Natural language search term")
    category: str | None = Field(default=None, description="Category slug to filter by")
    min_price: float | None = Field(default=None, ge=0, description="Minimum price filter")
    max_price: float | None = Field(default=None, ge=0, description="Maximum price filter")
    in_stock_only: bool = Field(default=False, description="Only return in-stock products")
    attributes: dict[str, str] = Field(default_factory=dict, description="Exact-match attribute filters")


class ProductIdInput(BaseModel):
    """Input schema for catalog.get_product and catalog.check_availability."""
    model_config = {"extra": "forbid"}
    product_id: str = Field(description="UUID of the product")


class VariantInput(BaseModel):
    """Input schema for catalog.get_variant."""
    model_config = {"extra": "forbid"}
    product_id: str = Field(description="UUID of the product")
    variant_id: str = Field(description="UUID of the variant")


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

@dataclass
class ToolDefinition:
    """A registered tool with schema and handler."""
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema
    input_model: type[BaseModel]  # Pydantic model for validation
    handler: Callable[..., Awaitable[ToolResult]]
    requires_policy: bool = False
    action_type: str | None = None


# ---------------------------------------------------------------------------
# Catalog tool handlers
# ---------------------------------------------------------------------------

def _serialize_for_model(obj: Any) -> Any:
    """Recursively convert Decimal/UUID to JSON-safe types."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _serialize_for_model(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_model(i) for i in obj]
    if hasattr(obj, "model_dump"):
        return _serialize_for_model(obj.model_dump())
    return obj


async def _handle_catalog_search(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]
) -> ToolResult:
    """Execute catalog.search using AICatalogService."""
    start = time.monotonic()
    try:
        validated = CatalogSearchInput(**args)
        req = AICatalogSearchRequest(
            query=validated.query,
            category=validated.category,
            min_price=Decimal(str(validated.min_price)) if validated.min_price is not None else None,
            max_price=Decimal(str(validated.max_price)) if validated.max_price is not None else None,
            in_stock_only=validated.in_stock_only,
            attributes=validated.attributes,
            limit=MAX_SEARCH_RESULTS,
            offset=0,
        )
        products, total = await AICatalogService.search(db, tenant_id, req)
        data = {
            "products": _serialize_for_model(products),
            "total": total,
            "returned": len(products),
        }
        return ToolResult(success=True, data=data, latency_ms=(time.monotonic() - start) * 1000)
    except PydanticValidationError as e:
        return ToolResult(success=False, error=f"Invalid arguments: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("catalog.search failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_get_product(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]
) -> ToolResult:
    """Execute catalog.get_product using AICatalogService."""
    start = time.monotonic()
    try:
        validated = ProductIdInput(**args)
        product_id = UUID(validated.product_id)
        product = await AICatalogService.get_product(db, tenant_id, product_id)
        return ToolResult(success=True, data=_serialize_for_model(product), latency_ms=(time.monotonic() - start) * 1000)
    except NotFoundError:
        return ToolResult(success=False, error="Product not found.", latency_ms=(time.monotonic() - start) * 1000)
    except (ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid arguments: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("catalog.get_product failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_get_variant(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]
) -> ToolResult:
    """Execute catalog.get_variant using AICatalogService."""
    start = time.monotonic()
    try:
        validated = VariantInput(**args)
        product = await AICatalogService.get_variant(
            db, tenant_id, UUID(validated.product_id), UUID(validated.variant_id)
        )
        return ToolResult(success=True, data=_serialize_for_model(product), latency_ms=(time.monotonic() - start) * 1000)
    except NotFoundError:
        return ToolResult(success=False, error="Variant not found.", latency_ms=(time.monotonic() - start) * 1000)
    except (ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid arguments: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("catalog.get_variant failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_check_availability(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]
) -> ToolResult:
    """Execute catalog.check_availability using AICatalogService."""
    start = time.monotonic()
    try:
        validated = ProductIdInput(**args)
        avail = await AICatalogService.check_availability(db, tenant_id, UUID(validated.product_id))
        return ToolResult(success=True, data=_serialize_for_model(avail), latency_ms=(time.monotonic() - start) * 1000)
    except NotFoundError:
        return ToolResult(success=False, error="Product not found.", latency_ms=(time.monotonic() - start) * 1000)
    except (ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid arguments: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("catalog.check_availability failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_get_relationships(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]
) -> ToolResult:
    """Execute catalog.get_relationships using AICatalogService."""
    start = time.monotonic()
    try:
        validated = ProductIdInput(**args)
        rels = await AICatalogService.get_relationships(db, tenant_id, UUID(validated.product_id))
        # Bound the number of relationships returned
        bounded = rels[:MAX_RELATIONSHIPS]
        return ToolResult(
            success=True,
            data={"relationships": _serialize_for_model(bounded), "total": len(rels)},
            latency_ms=(time.monotonic() - start) * 1000,
        )
    except NotFoundError:
        return ToolResult(success=False, error="Product not found.", latency_ms=(time.monotonic() - start) * 1000)
    except (ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid arguments: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("catalog.get_relationships failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


class CartItemInputSchema(BaseModel):
    model_config = {"extra": "forbid"}
    product_id: str = Field(description="UUID of the product to add")
    variant_id: str | None = Field(default=None, description="UUID of the variant (if applicable)")
    quantity: int = Field(default=1, gt=0, description="Quantity to add")
    confirmation_token: str | None = Field(default=None, description="Token provided by the user for confirmation")


class CartItemUpdateSchema(BaseModel):
    model_config = {"extra": "forbid"}
    item_id: str = Field(description="UUID of the cart item to update")
    quantity: int = Field(gt=0, description="New quantity")
    confirmation_token: str | None = Field(default=None, description="Token provided by the user for confirmation")


class CartItemIdInputSchema(BaseModel):
    model_config = {"extra": "forbid"}
    item_id: str = Field(description="UUID of the cart item")
    confirmation_token: str | None = Field(default=None, description="Token provided by the user for confirmation")


class CartClearInputSchema(BaseModel):
    model_config = {"extra": "forbid"}
    confirmation_token: str | None = Field(default=None, description="Token provided by the user for confirmation")


class EmptyInputSchema(BaseModel):
    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Cart tool handlers
# ---------------------------------------------------------------------------

async def _handle_cart_get(db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]) -> ToolResult:
    start = time.monotonic()
    try:
        cart = await CartService.get_or_create_cart(db, tenant_id, user_id)
        from app.api.routes.cart import _build_cart_response
        data = _serialize_for_model(_build_cart_response(cart))
        return ToolResult(success=True, data=data, latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("cart.get failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_cart_add_item(db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]) -> ToolResult:
    start = time.monotonic()
    try:
        validated = CartItemInputSchema(**args)
        item_create = CartItemCreate(
            product_id=UUID(validated.product_id),
            variant_id=UUID(validated.variant_id) if validated.variant_id else None,
            quantity=validated.quantity
        )
        async with db.begin_nested():
            await CartService.add_item(db, tenant_id, user_id, item_create, validated.confirmation_token)
        return ToolResult(success=True, data={"status": "success"}, latency_ms=(time.monotonic() - start) * 1000)
    except CartConfirmationRequired as e:
        # Expected flow: returning confirmation requirement
        return ToolResult(success=True, data={"status": "confirmation_required", "details": e.confirmation.model_dump(mode="json")}, latency_ms=(time.monotonic() - start) * 1000)
    except (CartError, ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid action: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("cart.add_item failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_cart_update_item(db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]) -> ToolResult:
    start = time.monotonic()
    try:
        validated = CartItemUpdateSchema(**args)
        item_update = CartItemUpdate(quantity=validated.quantity)
        async with db.begin_nested():
            await CartService.update_item(db, tenant_id, user_id, UUID(validated.item_id), item_update, validated.confirmation_token)
        return ToolResult(success=True, data={"status": "success"}, latency_ms=(time.monotonic() - start) * 1000)
    except CartConfirmationRequired as e:
        return ToolResult(success=True, data={"status": "confirmation_required", "details": e.confirmation.model_dump(mode="json")}, latency_ms=(time.monotonic() - start) * 1000)
    except (CartError, ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid action: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("cart.update_item failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_cart_remove_item(db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]) -> ToolResult:
    start = time.monotonic()
    try:
        validated = CartItemIdInputSchema(**args)
        async with db.begin_nested():
            await CartService.remove_item(db, tenant_id, user_id, UUID(validated.item_id), validated.confirmation_token)
        return ToolResult(success=True, data={"status": "success"}, latency_ms=(time.monotonic() - start) * 1000)
    except CartConfirmationRequired as e:
        return ToolResult(success=True, data={"status": "confirmation_required", "details": e.confirmation.model_dump(mode="json")}, latency_ms=(time.monotonic() - start) * 1000)
    except (CartError, ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid action: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("cart.remove_item failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_cart_clear(db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]) -> ToolResult:
    start = time.monotonic()
    try:
        validated = CartClearInputSchema(**args)
        async with db.begin_nested():
            await CartService.clear_cart(db, tenant_id, user_id, validated.confirmation_token)
        return ToolResult(success=True, data={"status": "success"}, latency_ms=(time.monotonic() - start) * 1000)
    except CartConfirmationRequired as e:
        return ToolResult(success=True, data={"status": "confirmation_required", "details": e.confirmation.model_dump(mode="json")}, latency_ms=(time.monotonic() - start) * 1000)
    except (CartError, ValueError, PydanticValidationError) as e:
        return ToolResult(success=False, error=f"Invalid action: {e}", latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("cart.clear failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


async def _handle_cart_validate(db: AsyncSession, tenant_id: UUID, user_id: UUID, args: dict[str, Any]) -> ToolResult:
    start = time.monotonic()
    try:
        res = await CartService.validate_cart(db, tenant_id, user_id)
        return ToolResult(success=True, data=_serialize_for_model(res), latency_ms=(time.monotonic() - start) * 1000)
    except Exception as e:
        logger.exception("cart.validate failed")
        return ToolResult(success=False, error=str(e), latency_ms=(time.monotonic() - start) * 1000)


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """
    Strict registry of tools available to the AI agent.

    - Rejects unknown tools.
    - Validates arguments against Pydantic schemas.
    - Rejects oversized inputs.
    - Injects tenant context from the session (never from the LLM).
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def get_openai_tool_schemas(self) -> list[dict[str, Any]]:
        """Return tool definitions in the format expected by LLM function calling."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            })
        return schemas

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> ToolResult:
        """
        Validate and execute a tool call.

        - Rejects unknown tools.
        - Validates argument size.
        - Validates arguments with Pydantic.
        - Injects db, tenant_id, and user_id (from session, never from LLM).
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        # Check input size
        raw = json.dumps(arguments, default=str)
        if len(raw.encode("utf-8")) > MAX_TOOL_INPUT_SIZE:
            return ToolResult(success=False, error="Tool input exceeds maximum allowed size.")

        # Validate with Pydantic
        try:
            tool.input_model(**arguments)
        except PydanticValidationError as e:
            return ToolResult(success=False, error=f"Invalid arguments: {e}")

        # Policy Engine Evaluation
        if tool.requires_policy:
            from app.services.policy_engine import PolicyEngineService
            action = tool.action_type or tool.name.upper().replace(".", "_")
            decision = await PolicyEngineService.evaluate(db, tenant_id, action, arguments)
            if decision.decision == "DENY":
                return ToolResult(
                    success=False, 
                    error=f"Policy violation: {', '.join(decision.reasons)}",
                )

        # Execute handler
        return await tool.handler(db, tenant_id, user_id, arguments)


# ---------------------------------------------------------------------------
# Factory: create a registry with all catalog tools
# ---------------------------------------------------------------------------

def create_catalog_tool_registry() -> ToolRegistry:
    """Build and return a ToolRegistry with the five catalog tools registered."""
    registry = ToolRegistry()

    registry.register(ToolDefinition(
        name="catalog.search",
        description=(
            "Search the product catalog. Supports natural language query, "
            "category slug, price range, stock filter, and exact attribute matching. "
            "Returns up to 5 products."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language search term"},
                "category": {"type": "string", "description": "Category slug to filter by"},
                "min_price": {"type": "number", "description": "Minimum price filter"},
                "max_price": {"type": "number", "description": "Maximum price filter"},
                "in_stock_only": {"type": "boolean", "description": "Only return in-stock products"},
                "attributes": {
                    "type": "object",
                    "description": "Key-value pairs for exact match filtering",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        input_model=CatalogSearchInput,
        handler=_handle_catalog_search,
    ))

    registry.register(ToolDefinition(
        name="catalog.get_product",
        description="Retrieve full details and variants of a specific product by its UUID.",
        input_schema={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "UUID of the product"},
            },
            "required": ["product_id"],
            "additionalProperties": False,
        },
        input_model=ProductIdInput,
        handler=_handle_get_product,
    ))

    registry.register(ToolDefinition(
        name="catalog.get_variant",
        description="Retrieve a specific variant of a product.",
        input_schema={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "UUID of the product"},
                "variant_id": {"type": "string", "description": "UUID of the variant"},
            },
            "required": ["product_id", "variant_id"],
            "additionalProperties": False,
        },
        input_model=VariantInput,
        handler=_handle_get_variant,
    ))

    registry.register(ToolDefinition(
        name="catalog.check_availability",
        description="Check current inventory availability for a product.",
        input_schema={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "UUID of the product"},
            },
            "required": ["product_id"],
            "additionalProperties": False,
        },
        input_model=ProductIdInput,
        handler=_handle_check_availability,
    ))

    registry.register(ToolDefinition(
        name="catalog.get_relationships",
        description="Retrieve product relationships (upsell, cross-sell, accessories) for a product.",
        input_schema={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "UUID of the product"},
            },
            "required": ["product_id"],
            "additionalProperties": False,
        },
        input_model=ProductIdInput,
        handler=_handle_get_relationships,
    ))

    registry.register(ToolDefinition(
        name="cart.get",
        description="Retrieve the current user's shopping cart.",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        input_model=EmptyInputSchema,
        handler=_handle_cart_get,
    ))

    registry.register(ToolDefinition(
        name="cart.add_item",
        description="Add a product to the cart. If a confirmation token is returned, ask the user to confirm using the details provided, and then re-call this tool with the token.",
        input_schema={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "UUID of the product"},
                "variant_id": {"type": "string", "description": "UUID of the variant (optional)"},
                "quantity": {"type": "integer", "description": "Quantity to add"},
                "confirmation_token": {"type": "string", "description": "Token to confirm mutation (leave empty on first call)"},
            },
            "required": ["product_id", "quantity"],
            "additionalProperties": False,
        },
        input_model=CartItemInputSchema,
        handler=_handle_cart_add_item,
        requires_policy=True,
    ))

    registry.register(ToolDefinition(
        name="cart.update_item",
        description="Update the quantity of an item in the cart. Requires confirmation token.",
        input_schema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "UUID of the cart item"},
                "quantity": {"type": "integer", "description": "New quantity"},
                "confirmation_token": {"type": "string", "description": "Token to confirm mutation (leave empty on first call)"},
            },
            "required": ["item_id", "quantity"],
            "additionalProperties": False,
        },
        input_model=CartItemUpdateSchema,
        handler=_handle_cart_update_item,
        requires_policy=True,
    ))

    registry.register(ToolDefinition(
        name="cart.remove_item",
        description="Remove an item from the cart. Requires confirmation token.",
        input_schema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "UUID of the cart item"},
                "confirmation_token": {"type": "string", "description": "Token to confirm mutation (leave empty on first call)"},
            },
            "required": ["item_id"],
            "additionalProperties": False,
        },
        input_model=CartItemIdInputSchema,
        handler=_handle_cart_remove_item,
        requires_policy=True,
    ))

    registry.register(ToolDefinition(
        name="cart.clear",
        description="Clear all items from the cart. Requires confirmation token.",
        input_schema={
            "type": "object",
            "properties": {
                "confirmation_token": {"type": "string", "description": "Token to confirm mutation (leave empty on first call)"},
            },
            "required": [],
            "additionalProperties": False,
        },
        input_model=CartClearInputSchema,
        handler=_handle_cart_clear,
        requires_policy=True,
    ))

    registry.register(ToolDefinition(
        name="cart.validate",
        description="Validate the cart (check for price changes and inventory availability).",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        input_model=EmptyInputSchema,
        handler=_handle_cart_validate,
    ))

    return registry
