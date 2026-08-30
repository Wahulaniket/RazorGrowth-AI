import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.user import User
from app.models.policy import Policy
from app.models.role import Role, Permission, RolePermission
from app.models.tenant_membership import TenantMembership


@pytest.fixture
async def policy_auth_headers(db: AsyncSession, tenant: Tenant, test_user: User):
    # Ensure role and membership exist with policy permissions
    role = await db.scalar(select(Role).where(Role.name == "PolicyAdmin"))
    if not role:
        role = Role(name="PolicyAdmin")
        db.add(role)
        await db.flush()
        
        perm_read = Permission(name="policies.read")
        perm_write = Permission(name="policies.write")
        perm_agent = Permission(name="agent.use")
        db.add_all([perm_read, perm_write, perm_agent])
        await db.flush()
        
        db.add_all([
            RolePermission(role_id=role.id, permission_id=perm_read.id),
            RolePermission(role_id=role.id, permission_id=perm_write.id),
            RolePermission(role_id=role.id, permission_id=perm_agent.id)
        ])
        await db.flush()
        
    mem = TenantMembership(user_id=test_user.id, tenant_id=tenant.id, role_id=role.id)
    db.add(mem)
    await db.flush()
    await db.refresh(test_user, ["memberships"])
    
    from app.core.security import create_access_token
    from datetime import timedelta
    access_token = create_access_token(
        data={"sub": str(test_user.id), "type": "access"},
        expires_delta=timedelta(minutes=15)
    )
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Tenant-ID": str(tenant.id)
    }


@pytest.mark.asyncio
async def test_create_policy(client: AsyncClient, policy_auth_headers, db: AsyncSession, tenant: Tenant):
    res = await client.post(
        "/api/v1/policies",
        headers=policy_auth_headers,
        json={
            "name": "Test Max Discount",
            "policy_type": "DISCOUNT_LIMIT",
            "level": "MERCHANT",
            "rules": {"max_discount_percent": 15},
            "is_active": True
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Max Discount"
    assert data["policy_type"] == "DISCOUNT_LIMIT"
    assert data["rules"]["max_discount_percent"] == 15
    assert "id" in data


@pytest.mark.asyncio
async def test_get_policies(client: AsyncClient, policy_auth_headers, db: AsyncSession, tenant: Tenant):
    # Assume the policy created above or create a new one
    policy = Policy(
        tenant_id=tenant.id,
        name="Test Get Policy",
        policy_type="TRANSACTION_LIMIT",
        rules={"max_amount": 1000}
    )
    db.add(policy)
    await db.commit()
    
    res = await client.get("/api/v1/policies", headers=policy_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert any(p["name"] == "Test Get Policy" for p in data)


@pytest.mark.asyncio
async def test_update_policy(client: AsyncClient, policy_auth_headers, db: AsyncSession, tenant: Tenant):
    policy = Policy(
        tenant_id=tenant.id,
        name="Test Update Policy",
        policy_type="TRANSACTION_LIMIT",
        rules={"max_amount": 500}
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    
    res = await client.patch(
        f"/api/v1/policies/{policy.id}",
        headers=policy_auth_headers,
        json={"rules": {"max_amount": 800}, "is_active": False}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["rules"]["max_amount"] == 800
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_evaluate_policy(client: AsyncClient, policy_auth_headers, db: AsyncSession, tenant: Tenant):
    # Create an active policy that limits discount to 20
    policy = Policy(
        tenant_id=tenant.id,
        name="Strict Discount Policy",
        policy_type="DISCOUNT_LIMIT",
        rules={"max_discount_percent": 20},
        is_active=True
    )
    db.add(policy)
    await db.commit()
    
    # 1. Allow case (discount is 10, which is < 20)
    res = await client.post(
        "/api/v1/internal/policy/evaluate",
        headers=policy_auth_headers,
        json={
            "action": "DISCOUNT",
            "context": {"discount_percent": 10}
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    
    # 2. Deny case (discount is 25, which is > 20)
    res = await client.post(
        "/api/v1/internal/policy/evaluate",
        headers=policy_auth_headers,
        json={
            "action": "DISCOUNT",
            "context": {"discount_percent": 25}
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "DENY"
    assert "EXCEEDS_MAX_DISCOUNT (Strict Discount Policy)" in data["reasons"]
