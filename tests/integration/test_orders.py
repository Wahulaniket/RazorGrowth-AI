import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.checkout import Order
from app.core.security import create_access_token
from app.models.tenant_membership import TenantMembership
from app.models.role import Role, Permission, RolePermission
from app.models.tenant import Tenant

@pytest.fixture
async def other_tenant(db: AsyncSession):
    t = Tenant(name="Other Tenant", slug="other-tenant")
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t

@pytest.fixture
async def setup_permissions(db: AsyncSession, tenant, test_user):
    role = await db.scalar(select(Role).where(Role.name == "Admin"))
    if not role:
        role = Role(name="Admin")
        db.add(role)
        await db.flush()
        
        perm_read = Permission(name="catalog.read")
        db.add(perm_read)
        await db.flush()
        
        db.add(RolePermission(role_id=role.id, permission_id=perm_read.id))
        await db.flush()
        
    mem = TenantMembership(user_id=test_user.id, tenant_id=tenant.id, role_id=role.id)
    db.add(mem)
    await db.commit()
    await db.refresh(test_user, ["memberships"])

@pytest.fixture
def test_auth_headers(test_user, tenant, setup_permissions):
    token = create_access_token(data={"sub": str(test_user.id), "tenant_id": str(tenant.id)})
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}

@pytest.fixture
def test_auth_headers_other_tenant(test_user, other_tenant):
    token = create_access_token(data={"sub": str(test_user.id), "tenant_id": str(other_tenant.id)})
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(other_tenant.id)}

@pytest.fixture
async def setup_orders(db: AsyncSession, tenant, test_user):
    order1 = Order(
        tenant_id=tenant.id,
        customer_id=test_user.id,
        currency="INR",
        subtotal=Decimal("100.00"),
        total=Decimal("118.00"),
        status="CREATED",
        payment_status="PAID"
    )
    order2 = Order(
        tenant_id=tenant.id,
        customer_id=test_user.id,
        currency="INR",
        subtotal=Decimal("200.00"),
        total=Decimal("236.00"),
        status="DELIVERED",
        payment_status="PAID"
    )
    db.add_all([order1, order2])
    await db.commit()
    return [order1, order2]

@pytest.mark.asyncio
async def test_get_orders_empty(client: AsyncClient, test_auth_headers):
    res = await client.get("/api/v1/orders/", headers=test_auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 0

@pytest.mark.asyncio
async def test_get_orders_authenticated(client: AsyncClient, test_auth_headers, setup_orders):
    res = await client.get("/api/v1/orders/", headers=test_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2

@pytest.mark.asyncio
async def test_get_order_by_id(client: AsyncClient, test_auth_headers, setup_orders):
    order_id = str(setup_orders[0].id)
    res = await client.get(f"/api/v1/orders/{order_id}", headers=test_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == order_id
    assert data["total"] == "118.00"

@pytest.mark.asyncio
async def test_get_orders_unauthorized(client: AsyncClient):
    res = await client.get("/api/v1/orders/")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_get_orders_tenant_isolation(client: AsyncClient, test_auth_headers_other_tenant, setup_orders):
    res = await client.get("/api/v1/orders/", headers=test_auth_headers_other_tenant)
    assert res.status_code in (401, 403)

@pytest.mark.asyncio
async def test_get_order_tenant_isolation(client: AsyncClient, test_auth_headers_other_tenant, setup_orders):
    order_id = str(setup_orders[0].id)
    res = await client.get(f"/api/v1/orders/{order_id}", headers=test_auth_headers_other_tenant)
    assert res.status_code in (401, 403)
