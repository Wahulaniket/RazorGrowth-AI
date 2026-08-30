import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools import ToolDefinition, ToolResult
from app.models.tenant import Tenant
from app.models.user import User

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def admin_auth_headers(
    db: AsyncSession, test_user: User, test_tenant: Tenant
) -> dict:
    from sqlalchemy import select
    from app.models.role import Role, Permission, RolePermission
    from app.models.tenant_membership import TenantMembership
    from app.core.security import create_access_token

    # Create role with policies permissions
    role = (await db.execute(select(Role).where(Role.name == "Admin"))).scalar_one_or_none()
    if not role:
        role = Role(name="Admin")
        db.add(role)
        await db.flush()

    for p_name in ["policies.read", "policies.write", "agent.use"]:
        perm = (await db.execute(select(Permission).where(Permission.name == p_name))).scalar_one_or_none()
        if not perm:
            perm = Permission(name=p_name)
            db.add(perm)
            await db.flush()
        
        rp = (await db.execute(select(RolePermission).where(RolePermission.role_id == role.id, RolePermission.permission_id == perm.id))).scalar_one_or_none()
        if not rp:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    mem = (await db.execute(select(TenantMembership).where(TenantMembership.user_id == test_user.id, TenantMembership.tenant_id == test_tenant.id))).scalar_one_or_none()
    if not mem:
        db.add(TenantMembership(user_id=test_user.id, tenant_id=test_tenant.id, role_id=role.id))
    else:
        mem.role_id = role.id
    await db.commit()
    await db.refresh(test_user, ["memberships"])

    token = create_access_token(data={"sub": str(test_user.id), "email": test_user.email})
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}

async def test_agent_policy_denial_blocks_tool(
    client: AsyncClient,
    admin_auth_headers: dict,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    # This test verifies that policy denial prevents the underlying mutation
    # and the LLM is forced to respect it.
    
    # 1. Create a strict policy (max_amount = 0)
    payload = {
        "name": "Strict Payment Limit",
        "policy_type": "TRANSACTION_LIMIT",
        "level": "MERCHANT",
        "rules": {"max_amount": 0},
        "is_active": True
    }
    resp = await client.post("/api/v1/policies", json=payload, headers=admin_auth_headers)
    assert resp.status_code == 201

    # 2. Define a dummy tool that requires policy (PAYMENT)
    from pydantic import BaseModel, Field
    class DummyPaymentInput(BaseModel):
        amount: int = Field(...)
        
    async def _dummy_payment(db, tenant_id, user_id, args):
        return ToolResult(success=True, data={"status": "paid"})
        
    tool_def = ToolDefinition(
        name="payment.execute",
        description="Execute a payment.",
        input_schema={
            "type": "object",
            "properties": {"amount": {"type": "integer"}},
            "required": ["amount"]
        },
        input_model=DummyPaymentInput,
        handler=_dummy_payment,
        requires_policy=True,
        action_type="PAYMENT"
    )
    
    from app.agents.tools import ToolRegistry
    registry = ToolRegistry()
    registry.register(tool_def)
    
    # 3. Simulate the agent orchestrator executing the tool
    # LLM attempts to bypass or invoke directly
    args = {"amount": 500}
    
    # Tool execution MUST fail because amount > 0 and policy DENY
    result = await registry.execute(
        "payment.execute",
        args,
        db,
        test_tenant.id,
        test_user.id
    )
    
    assert result.success is False
    assert "Policy violation" in result.error
    assert "EXCEEDS_MAX_AMOUNT" in result.error
