import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
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
async def test_create_policy_success(
    client: AsyncClient,
    db: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
    admin_auth_headers: dict,
):
    payload = {
        "name": "Strict Payment Limit",
        "policy_type": "TRANSACTION_LIMIT",
        "level": "MERCHANT",
        "rules": {"max_amount": 100000},
        "is_active": True
    }
    
    response = await client.post("/api/v1/policies", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Strict Payment Limit"
    assert data["policy_type"] == "TRANSACTION_LIMIT"
    assert data["rules"]["max_amount"] == 100000
    
    policy_id = data["id"]
    
    # Check DB
    stmt = select(Policy).where(Policy.id == policy_id)
    policy = (await db.execute(stmt)).scalar_one_or_none()
    assert policy is not None
    assert policy.tenant_id == test_tenant.id

async def test_get_policies_success(
    client: AsyncClient,
    admin_auth_headers: dict,
):
    response = await client.get("/api/v1/policies", headers=admin_auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    
async def test_policy_evaluation_internal(
    client: AsyncClient,
    admin_auth_headers: dict,
):
    # Create the policy first
    payload = {
        "name": "Strict Payment Limit",
        "policy_type": "TRANSACTION_LIMIT",
        "level": "MERCHANT",
        "rules": {"max_amount": 100000},
        "is_active": True
    }
    await client.post("/api/v1/policies", json=payload, headers=admin_auth_headers)

    # This acts as an integration test for the internal evaluation endpoint
    eval_payload = {
        "action": "PAYMENT",
        "context": {
            "session_id": "sess_123",
            "amount": 150000,
            "currency": "INR"
        }
    }
    
    response = await client.post("/api/v1/internal/policy/evaluate", json=eval_payload, headers=admin_auth_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    
    assert data["decision"] == "DENY"
    assert "EXCEEDS_MAX_AMOUNT" in data["reasons"][0]
