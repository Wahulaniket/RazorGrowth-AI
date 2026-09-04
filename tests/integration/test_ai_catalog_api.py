import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.tenant import Tenant
from app.models.user import User
from app.models.tenant_membership import TenantMembership
from app.models.role import Role
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.product_relationship import ProductRelationship

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def setup_catalog(db: AsyncSession, test_tenant: Tenant, test_user: User):
    # Create role and membership
    role_res = await db.execute(select(Role).where(Role.name == "Admin"))
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(name="Admin")
        db.add(role)
        await db.flush()
    
    db.info["tenant_id"] = str(test_tenant.id)
    
    mem = TenantMembership(user_id=test_user.id, tenant_id=test_tenant.id, role_id=role.id)
    db.add(mem)
    
    # Create category
    cat = Category(tenant_id=test_tenant.id, name="Electronics", slug="electronics")
    db.add(cat)
    await db.flush()
    
    # Create active product
    p1 = Product(
        tenant_id=test_tenant.id,
        category_id=cat.id,
        sku="LAP-001",
        name="Pro Laptop",
        slug="pro-laptop",
        description="High performance laptop for developers",
        brand="TechCorp",
        base_price=Decimal("1500.00"),
        status="ACTIVE",
        metadata_={"ram": "16GB", "storage": "512GB"}
    )
    db.add(p1)
    
    # Create inactive product
    p2 = Product(
        tenant_id=test_tenant.id,
        category_id=cat.id,
        sku="LAP-OLD",
        name="Old Laptop",
        slug="old-laptop",
        description="Discontinued",
        brand="TechCorp",
        base_price=Decimal("500.00"),
        status="INACTIVE"
    )
    db.add(p2)
    
    await db.flush()
    
    # Create inventory for p1
    inv = Inventory(
        tenant_id=test_tenant.id,
        product_id=p1.id,
        available_quantity=10,
        reserved_quantity=2
    )
    db.add(inv)
    
    # Create variant for p1
    v1 = ProductVariant(
        tenant_id=test_tenant.id,
        product_id=p1.id,
        sku="LAP-001-16GB",
        name="Pro Laptop 16GB",
        price=Decimal("1500.00"),
        attributes={"ram": "16GB"}
    )
    db.add(v1)
    
    await db.commit()
    
    # Refresh user to ensure relationships (like memberships) are updated in identity map
    await db.refresh(test_user, ['memberships'])
    
    return {
        "cat": cat,
        "p1": p1,
        "p2": p2,
        "v1": v1,
        "role": role,
        "mem": mem
    }

async def test_search_catalog(client: AsyncClient, db: AsyncSession, setup_catalog, test_tenant, test_user):
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}
    
    # 1. Search without filters
    res = await client.post("/api/v1/catalog/search", json={}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1  # Only ACTIVE product is returned
    assert data["items"][0]["name"] == "Pro Laptop"
    assert data["items"][0]["category"] == "electronics"
    assert float(data["items"][0]["price"]) == 1500.0
    
    # 2. Search by lexical query (ILIKE)
    res = await client.post("/api/v1/catalog/search", json={"query": "developer"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    
    res = await client.post("/api/v1/catalog/search", json={"query": "gaming"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0
    
    # 3. Filter by category
    res = await client.post("/api/v1/catalog/search", json={"category": "electronics"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    
    res = await client.post("/api/v1/catalog/search", json={"category": "home-appliances"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0
    
    # 4. Filter by price
    res = await client.post("/api/v1/catalog/search", json={"min_price": 1000, "max_price": 2000}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    
    # 5. Filter by in_stock_only
    res = await client.post("/api/v1/catalog/search", json={"in_stock_only": True}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    
    # 6. Filter by attributes
    res = await client.post("/api/v1/catalog/search", json={"attributes": {"ram": "16GB"}}, headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1


async def test_get_product_endpoints(client: AsyncClient, db: AsyncSession, setup_catalog, test_tenant, test_user):
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(test_tenant.id)}
    
    p1 = setup_catalog["p1"]
    v1 = setup_catalog["v1"]
    
    # 1. Get product
    res = await client.get(f"/api/v1/catalog/products/{p1.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(p1.id)
    assert len(data["variants"]) == 1
    assert data["variants"][0]["id"] == str(v1.id)
    
    # 2. Get variant
    res = await client.get(f"/api/v1/catalog/products/{p1.id}/variants/{v1.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(v1.id)
    
    # 3. Check availability
    res = await client.get(f"/api/v1/catalog/products/{p1.id}/availability", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["available_quantity"] == 10
    assert data["reserved_quantity"] == 2
    assert data["in_stock"] is True


async def test_tenant_isolation(client: AsyncClient, db: AsyncSession, setup_catalog, test_tenant, test_user):
    # Create tenant B
    tenant_b = Tenant(name="Tenant B", slug="tenant-b", default_currency="USD", timezone="UTC")
    db.add(tenant_b)
    
    user_b = User(email="userb@example.com", name="User B", password_hash="hash")
    db.add(user_b)
    await db.flush()
    
    db.info["tenant_id"] = str(tenant_b.id)
    from sqlalchemy import text
    await db.execute(text("SELECT set_config('app.current_tenant', :t, true)"), {"t": str(tenant_b.id)})
    
    mem_b = TenantMembership(user_id=user_b.id, tenant_id=tenant_b.id, role_id=setup_catalog["role"].id)
    db.add(mem_b)
    
    cat_b = Category(tenant_id=tenant_b.id, name="Books", slug="books")
    db.add(cat_b)
    await db.flush()
    
    p_b = Product(
        tenant_id=tenant_b.id, category_id=cat_b.id, sku="BOOK-001",
        name="Tenant B Book", slug="tenant-b-book", status="ACTIVE", base_price=Decimal("10.0")
    )
    db.add(p_b)
    await db.commit()
    
    from app.core.security import create_access_token
    token_a = create_access_token({"sub": str(test_user.id)})
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": str(test_tenant.id)}
    
    # Restore RLS context to test_tenant (since tests share one transaction)
    await db.execute(text("SELECT set_config('app.current_tenant', :t, true)"), {"t": str(test_tenant.id)})
    
    # User A searches - should NOT see Tenant B's book
    res = await client.post("/api/v1/catalog/search", json={}, headers=headers_a)
    assert res.status_code == 200
    names = [p["name"] for p in res.json()["items"]]
    assert "Tenant B Book" not in names
    assert "Pro Laptop" in names
    
    # User A tries to explicitly fetch Tenant B's product
    res = await client.get(f"/api/v1/catalog/products/{p_b.id}", headers=headers_a)
    assert res.status_code == 404
    
    # Unauthenticated access
    res = await client.post("/api/v1/catalog/search", json={}, headers={"X-Tenant-ID": str(test_tenant.id)})
    assert res.status_code == 401
    
    # Unauthorized tenant access (User A trying to query Tenant B's context)
    headers_unauth = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": str(tenant_b.id)}
    res = await client.post("/api/v1/catalog/search", json={}, headers=headers_unauth)
    assert res.status_code == 403
