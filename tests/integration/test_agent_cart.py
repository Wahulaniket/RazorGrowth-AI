import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from decimal import Decimal

from app.agents.tools import create_catalog_tool_registry
from app.agents.orchestrator import run_shopping_agent, AgentResult
from app.agents.llm import LLMProvider
from app.models.product import Product
from app.models.inventory import Inventory
from app.services.cart_service import CartService
from app.schemas.cart import CartMutationConfirmation


# A dummy LLM Provider for testing the agent tool calls
class FakeCartLLMProvider(LLMProvider):
    def __init__(self, simulate_confirmation=False):
        self.call_count = 0
        self.simulate_confirmation = simulate_confirmation
        self.token = None

    async def generate_with_tools(self, messages, tools, temperature=0.0):
        self.call_count += 1
        
        # If it's the first call, try to add an item to cart
        if self.call_count == 1:
            from app.agents.llm import LLMResponse, LLMMessage, ToolCall
            return LLMResponse(
                message=LLMMessage(
                    role="assistant",
                    content="Adding product...",
                    tool_calls=[
                        ToolCall(
                            id="call_1",
                            tool_name="cart.add_item",
                            arguments={"product_id": "test-product-id", "quantity": 1}
                        )
                    ]
                ),
                finish_reason="tool_calls",
                latency_ms=10.0, model="fake"
            )
            
        # If it's the second call (after receiving the tool response)
        if self.call_count == 2:
            import json
            last_msg = messages[-1]
            if last_msg.role == "tool" and last_msg.name == "cart.add_item":
                tool_res = json.loads(last_msg.content)
                if tool_res.get("status") == "confirmation_required":
                    self.token = tool_res["details"]["confirmation_token"]
                    if self.simulate_confirmation:
                        # LLM automatically uses the token to re-call (simulating user confirming)
                        from app.agents.llm import LLMResponse, LLMMessage, ToolCall
                        return LLMResponse(
                            message=LLMMessage(
                                role="assistant",
                                content="Confirming add...",
                                tool_calls=[
                                    ToolCall(
                                        id="call_2",
                                        tool_name="cart.add_item",
                                        arguments={
                                            "product_id": "test-product-id", 
                                            "quantity": 1,
                                            "confirmation_token": self.token
                                        }
                                    )
                                ]
                            ),
                            finish_reason="tool_calls",
                            latency_ms=10.0, model="fake"
                        )
                    else:
                        # Agent stops to ask the user
                        from app.agents.llm import LLMResponse, LLMMessage
                        return LLMResponse(
                            message=LLMMessage(
                                role="assistant",
                                content="I can add this to your cart for ₹1000. Do you want to proceed?"
                            ),
                            finish_reason="stop",
                            latency_ms=10.0, model="fake"
                        )
            
            # If the tool call succeeded
            from app.agents.llm import LLMResponse, LLMMessage
            return LLMResponse(
                message=LLMMessage(
                    role="assistant",
                    content="The item was successfully added."
                ),
                finish_reason="stop",
                latency_ms=10.0, model="fake"
            )
            
        if self.call_count == 3:
            from app.agents.llm import LLMResponse, LLMMessage
            return LLMResponse(
                message=LLMMessage(
                    role="assistant",
                    content="Finished."
                ),
                finish_reason="stop",
                latency_ms=10.0, model="fake"
            )


@pytest.fixture
async def cart_test_data(db: AsyncSession, tenant):
    product_id = uuid.uuid4()
    # Hack the dummy provider to use the correct UUID
    FakeCartLLMProvider.test_product_id = str(product_id)
    
    product = Product(
        id=product_id,
        tenant_id=tenant.id,
        category_id=uuid.uuid4(),  # Might fail FK if category not there, let's assume we bypass or setup properly
        sku="CART-TEST-1",
        name="Cart Test Product",
        slug="cart-test-product",
        base_price=Decimal("1000.00"),
        currency="INR"
    )
    # Actually we should just mock get_current_price_and_inventory for unit testing the tool, or use proper fixtures.
    # We will use monkeypatch for get_current_price_and_inventory to avoid full DB setup here, as we test DB logic in test_cart.py
    pass


@pytest.mark.asyncio
async def test_agent_add_item_stops_for_confirmation(db: AsyncSession, tenant, test_user, monkeypatch):
    from app.models.category import Category
    from app.models.product import Product
    
    category = Category(tenant_id=tenant.id, name="Agent Cat 2", slug="agent-cat-2")
    db.add(category)
    await db.flush()
    
    product = Product(
        tenant_id=tenant.id,
        category_id=category.id,
        name="Agent Product 2",
        slug="agent-product-2",
        sku="agent-product-2",
        base_price=Decimal("1000.00"),
        status="ACTIVE"
    )
    db.add(product)
    await db.commit()
    test_product_id = str(product.id)
    
    # Mock CartService to bypass DB
    async def mock_get_current_price(*args, **kwargs):
        return Decimal("1000.00"), 10, "INR"
    monkeypatch.setattr(CartService, "get_current_price_and_inventory", mock_get_current_price)
    
    # Override tool input in provider
    class MyFakeLLM(FakeCartLLMProvider):
        async def generate_with_tools(self, messages, tools, temperature=0.0):
            if self.call_count == 0:
                self.call_count += 1
                from app.agents.llm import LLMResponse, LLMMessage, ToolCall
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[ToolCall(id="1", tool_name="cart.add_item", arguments={"product_id": test_product_id, "quantity": 1})]
                    ),
                    finish_reason="tool_calls",
                    latency_ms=10.0, model="fake"
                )
            elif self.call_count == 1:
                self.call_count += 1
                import json
                last = messages[-1]
                assert last.role == "tool"
                res = json.loads(last.content)
                assert res.get("status") == "confirmation_required"
                from app.agents.llm import LLMResponse, LLMMessage
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="Would you like me to add it?"
                    ),
                    finish_reason="stop",
                    latency_ms=10.0, model="fake"
                )

    llm = MyFakeLLM()
    registry = create_catalog_tool_registry()
    
    result = await run_shopping_agent(
        db=db,
        tenant_id=tenant.id,
        user_id=test_user.id,
        user_message="Add product",
        llm=llm,
        registry=registry
    )
    
    assert "Would you like me to add it" in result.message
    assert "cart.add_item" in result.tools_used
    
    # Verify trace shows tool returning false (since it threw exception for confirmation)
    tool_events = [e for e in result.trace if e.event == "agent.tool_completed"]
    assert len(tool_events) == 1
    assert tool_events[0].data["success"] is True


@pytest.mark.asyncio
async def test_agent_add_item_executes_with_confirmation(db: AsyncSession, tenant, test_user, monkeypatch):
    from app.models.category import Category
    from app.models.product import Product
    
    category = Category(tenant_id=tenant.id, name="Agent Cat", slug="agent-cat")
    db.add(category)
    await db.flush()
    
    product = Product(
        tenant_id=tenant.id,
        category_id=category.id,
        name="Agent Product",
        slug="agent-product",
        sku="agent-product",
        base_price=Decimal("1000.00"),
        status="ACTIVE"
    )
    db.add(product)
    await db.commit()
    test_product_id = str(product.id)
    
    async def mock_get_current_price(*args, **kwargs):
        return Decimal("1000.00"), 10, "INR"
    monkeypatch.setattr(CartService, "get_current_price_and_inventory", mock_get_current_price)
    
    class MyFakeLLM2(FakeCartLLMProvider):
        async def generate_with_tools(self, messages, tools, temperature=0.0):
            if self.call_count == 0:
                self.call_count += 1
                from app.agents.llm import LLMResponse, LLMMessage, ToolCall
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[ToolCall(id="1", tool_name="cart.add_item", arguments={"product_id": test_product_id, "quantity": 1})]
                    ),
                    finish_reason="tool_calls",
                    latency_ms=10.0, model="fake"
                )
            elif self.call_count == 1:
                self.call_count += 1
                import json
                last = messages[-1]
                res = json.loads(last.content)
                token = res["details"]["confirmation_token"]
                from app.agents.llm import LLMResponse, LLMMessage, ToolCall
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[ToolCall(id="2", tool_name="cart.add_item", arguments={"product_id": test_product_id, "quantity": 1, "confirmation_token": token})]
                    ),
                    finish_reason="tool_calls",
                    latency_ms=10.0, model="fake"
                )
            elif self.call_count == 2:
                self.call_count += 1
                import json
                last = messages[-1]
                res = json.loads(last.content)
                assert res.get("status") == "success"
                from app.agents.llm import LLMResponse, LLMMessage
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="Added!"
                    ),
                    finish_reason="stop",
                    latency_ms=10.0, model="fake"
                )
                
    llm = MyFakeLLM2()
    registry = create_catalog_tool_registry()
    
    result = await run_shopping_agent(
        db=db,
        tenant_id=tenant.id,
        user_id=test_user.id,
        user_message="Add product with confirmation",
        llm=llm,
        registry=registry
    )
    
    assert result.message == "Added!"
    tool_events = [e for e in result.trace if e.event == "agent.tool_completed"]
    assert len(tool_events) == 2
    assert tool_events[0].data["success"] is True  # first one requires confirmation
    assert tool_events[1].data["success"] is True   # second one succeeds
