import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from uuid import uuid4

from app.models.tenant import Tenant
from app.models.user import User
from app.models.tenant_membership import TenantMembership
from app.models.role import Role, Permission, RolePermission
from app.models.product import Product

pytestmark = pytest.mark.asyncio

async def setup_test_data(db: AsyncSession, test_user: User, test_tenant: Tenant):
    viewer_role = await db.scalar(select(Role).where(Role.name == "Viewer"))
    if not viewer_role:
        viewer_role = Role(name="Viewer", description="Read-only")
        db.add(viewer_role)
        await db.flush()
    
    perms = {}
    for p_name in ["catalog.read", "catalog.write", "agent.use"]:
        p = await db.scalar(select(Permission).where(Permission.name == p_name))
        if not p:
            p = Permission(name=p_name)
            db.add(p)
            await db.flush()
        perms[p_name] = p
    
    rp = await db.scalar(select(RolePermission).where(RolePermission.role_id == viewer_role.id, RolePermission.permission_id == perms["catalog.read"].id))
    if not rp:
        db.add(RolePermission(role_id=viewer_role.id, permission_id=perms["catalog.read"].id))
    
    db.info["tenant_id"] = str(test_tenant.id)
    
    mem = TenantMembership(user_id=test_user.id, tenant_id=test_tenant.id, role_id=viewer_role.id)
    mem.role = viewer_role
    db.add(mem)
    test_user.memberships.append(mem)
    
    from app.models.category import Category
    cat = Category(tenant_id=test_tenant.id, name="Test Cat", slug="test-cat")
    db.add(cat)
    await db.flush()
    
    prod = Product(tenant_id=test_tenant.id, sku="SKU1", name="Product 1", slug="product-1", base_price=10.0, currency="USD", status="ACTIVE", category_id=cat.id)
    db.add(prod)
    
    await db.commit()
    return prod

async def test_rbac_viewer_permissions(client: AsyncClient, db: AsyncSession, test_user: User, test_tenant: Tenant):
    prod = await setup_test_data(db, test_user, test_tenant)
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    
    res = await client.get(
        "/api/v1/products", 
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}
    )
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1
    
    res = await client.post(
        "/api/v1/products", 
        json={"sku": "SKU2", "name": "Product 2", "price": 20.0, "currency": "USD", "category_id": None},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}
    )
    assert res.status_code == 403
    
    res = await client.put(
        f"/api/v1/products/{prod.id}", 
        json={"name": "Updated"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}
    )
    assert res.status_code == 403
    
    res = await client.post(
        "/api/v1/agent/chat",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}
    )
    assert res.status_code == 403
    
async def test_rls_missing_context(db: AsyncSession, test_tenant: Tenant):
    db.info.pop("tenant_id", None)
    
    res = await db.execute(text("SELECT * FROM inventory;"))
    assert len(res.fetchall()) == 0
    
    res = await db.execute(text("SELECT * FROM carts;"))
    assert len(res.fetchall()) == 0
    
    res = await db.execute(text("SELECT * FROM cart_items;"))
    assert len(res.fetchall()) == 0
    
    res = await db.execute(text("SELECT * FROM product_relationships;"))
    assert len(res.fetchall()) == 0
    
    from sqlalchemy.exc import DBAPIError
    try:
        await db.execute(text("INSERT INTO carts (id, tenant_id, status, currency, created_at, updated_at) VALUES (gen_random_uuid(), gen_random_uuid(), 'ACTIVE', 'USD', now(), now());"))
        assert False, "Should have failed due to RLS"
    except DBAPIError as e:
        assert "new row violates row-level security policy" in str(e)
