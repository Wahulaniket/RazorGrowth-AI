import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from decimal import Decimal
from datetime import timedelta

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.inventory import Inventory
from app.services.cart_service import CartService
from app.core.security import create_access_token


from app.models.category import Category
from app.models.tenant_membership import TenantMembership
from app.models.role import Role
from sqlalchemy import select

@pytest.fixture
async def setup_cart_data(db: AsyncSession, test_user, tenant):
    # Ensure role and membership exist for test_user
    role = await db.scalar(select(Role).where(Role.name == "Admin"))
    if not role:
        role = Role(name="Admin")
        db.add(role)
        await db.flush()
        
        from app.models.role import Permission, RolePermission
        perm_read = Permission(name="catalog.read")
        perm_write = Permission(name="catalog.write")
        db.add_all([perm_read, perm_write])
        await db.flush()
        
        db.add(RolePermission(role_id=role.id, permission_id=perm_read.id))
        db.add(RolePermission(role_id=role.id, permission_id=perm_write.id))
        await db.flush()
        
    mem = TenantMembership(user_id=test_user.id, tenant_id=tenant.id, role_id=role.id)
    db.add(mem)
    await db.flush()
    await db.refresh(test_user, ["memberships"])

    # Create category
    category = Category(
        tenant_id=tenant.id,
        name="Test Category",
        slug="test-category"
    )
    db.add(category)
    await db.flush()


    # Create product A
    product_a = Product(
        tenant_id=tenant.id,
        category_id=category.id,
        sku="TEST-SKU-A",
        name="Test Product A",
        slug="test-product-a",
        base_price=Decimal("1000.00"),
        currency="INR"
    )
    db.add(product_a)
    
    # Create product B
    product_b = Product(
        tenant_id=tenant.id,
        category_id=category.id,
        sku="TEST-SKU-B",
        name="Test Product B",
        slug="test-product-b",
        base_price=Decimal("2000.00"),
        currency="INR"
    )
    db.add(product_b)
    
    await db.flush()

    
    # Add inventory
    inv_a = Inventory(
        tenant_id=tenant.id,
        product_id=product_a.id,
        available_quantity=10,
        reserved_quantity=0
    )
    inv_b = Inventory(
        tenant_id=tenant.id,
        product_id=product_b.id,
        available_quantity=5,
        reserved_quantity=0
    )
    db.add(inv_a)
    db.add(inv_b)
    
    await db.commit()
    
    return {
        "product_a": product_a,
        "product_b": product_b,
        "inv_a": inv_a,
        "inv_b": inv_b,
        "category": category
    }

@pytest.fixture
def test_auth_headers(test_user, tenant):
    token = create_access_token(data={"sub": str(test_user.id), "tenant_id": str(tenant.id)})
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}


@pytest.mark.asyncio
async def test_get_cart_empty(client: AsyncClient, test_auth_headers, setup_cart_data):
    resp = await client.get("/api/v1/cart/", headers=test_auth_headers)
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["items"] == []
    assert data["cart_total"] == "0"


@pytest.mark.asyncio
async def test_add_item_requires_confirmation(client: AsyncClient, test_auth_headers, setup_cart_data):
    product_a = setup_cart_data["product_a"]
    
    resp = await client.post(
        "/api/v1/cart/items",
        headers=test_auth_headers,
        json={"product_id": str(product_a.id), "quantity": 1}
    )
    
    assert resp.status_code == 402  # Payment Required is used for confirmation required
    data = resp.json()
    assert "confirmation_token" in data["detail"]
    assert data["detail"]["action"] == "add_item"
    assert data["detail"]["current_price"] == "1000.00"


@pytest.mark.asyncio
async def test_add_item_with_confirmation(client: AsyncClient, test_auth_headers, setup_cart_data):
    product_a = setup_cart_data["product_a"]
    
    # 1. Ask for confirmation
    resp = await client.post(
        "/api/v1/cart/items",
        headers=test_auth_headers,
        json={"product_id": str(product_a.id), "quantity": 2}
    )
    assert resp.status_code == 402
    token = resp.json()["detail"]["confirmation_token"]
    
    # 2. Confirm
    resp = await client.post(
        f"/api/v1/cart/items?confirmation_token={token}",
        headers=test_auth_headers,
        json={"product_id": str(product_a.id), "quantity": 2}
    )
    
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == str(product_a.id)
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price_snapshot"] == "1000.00"
    assert data["items"][0]["line_total"] == "2000.00"
    assert data["cart_total"] == "2000.00"


@pytest.mark.asyncio
async def test_add_item_price_change_rejects_confirmation(
    client: AsyncClient, test_auth_headers, setup_cart_data, db: AsyncSession
):
    product_a = setup_cart_data["product_a"]
    
    # 1. Ask for confirmation
    resp = await client.post(
        "/api/v1/cart/items",
        headers=test_auth_headers,
        json={"product_id": str(product_a.id), "quantity": 1}
    )
    assert resp.status_code == 402
    token = resp.json()["detail"]["confirmation_token"]
    
    # 2. Simulate price change in DB
    product_a.base_price = Decimal("1200.00")
    db.add(product_a)
    await db.commit()
    
    # 3. Attempt confirmation with old token
    resp = await client.post(
        f"/api/v1/cart/items?confirmation_token={token}",
        headers=test_auth_headers,
        json={"product_id": str(product_a.id), "quantity": 1}
    )
    
    assert resp.status_code == 400
    assert "PRICE_CHANGED" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_add_item_insufficient_stock(client: AsyncClient, test_auth_headers, setup_cart_data):
    product_b = setup_cart_data["product_b"]  # Has 5 in stock
    
    resp = await client.post(
        "/api/v1/cart/items",
        headers=test_auth_headers,
        json={"product_id": str(product_b.id), "quantity": 10}
    )
    
    assert resp.status_code == 400
    assert "Insufficient inventory" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_item_quantity(client: AsyncClient, test_auth_headers, setup_cart_data):
    product_a = setup_cart_data["product_a"]
    
    # 1. Add
    resp = await client.post("/api/v1/cart/items", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    token = resp.json()["detail"]["confirmation_token"]
    resp = await client.post(f"/api/v1/cart/items?confirmation_token={token}", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    item_id = resp.json()["items"][0]["id"]
    
    # 2. Update without token
    resp = await client.put(f"/api/v1/cart/items/{item_id}", headers=test_auth_headers, json={"quantity": 3})
    assert resp.status_code == 402
    token = resp.json()["detail"]["confirmation_token"]
    
    # 3. Update with token
    resp = await client.put(f"/api/v1/cart/items/{item_id}?confirmation_token={token}", headers=test_auth_headers, json={"quantity": 3})
    assert resp.status_code == 200, resp.json()
    assert resp.json()["items"][0]["quantity"] == 3
    assert resp.json()["cart_total"] == "3000.00"


@pytest.mark.asyncio
async def test_remove_item(client: AsyncClient, test_auth_headers, setup_cart_data):
    product_a = setup_cart_data["product_a"]
    
    resp = await client.post("/api/v1/cart/items", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    token = resp.json()["detail"]["confirmation_token"]
    resp = await client.post(f"/api/v1/cart/items?confirmation_token={token}", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    item_id = resp.json()["items"][0]["id"]
    
    # Remove without token
    resp = await client.delete(f"/api/v1/cart/items/{item_id}", headers=test_auth_headers)
    assert resp.status_code == 402
    token = resp.json()["detail"]["confirmation_token"]
    
    # Remove with token
    resp = await client.delete(f"/api/v1/cart/items/{item_id}?confirmation_token={token}", headers=test_auth_headers)
    assert resp.status_code == 200, resp.json()
    assert len(resp.json()["items"]) == 0


@pytest.mark.asyncio
async def test_clear_cart(client: AsyncClient, test_auth_headers, setup_cart_data):
    product_a = setup_cart_data["product_a"]
    
    resp = await client.post("/api/v1/cart/items", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    token = resp.json()["detail"]["confirmation_token"]
    await client.post(f"/api/v1/cart/items?confirmation_token={token}", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    
    # Clear without token
    resp = await client.delete("/api/v1/cart/", headers=test_auth_headers)
    assert resp.status_code == 402
    token = resp.json()["detail"]["confirmation_token"]
    
    # Clear with token
    resp = await client.delete(f"/api/v1/cart/?confirmation_token={token}", headers=test_auth_headers)
    assert resp.status_code == 200, resp.json()
    assert len(resp.json()["items"]) == 0


@pytest.mark.asyncio
async def test_tampered_token_is_rejected(client: AsyncClient, test_auth_headers, setup_cart_data, test_user, tenant):
    product_a = setup_cart_data["product_a"]
    product_b = setup_cart_data["product_b"]
    
    # Get a valid token for product A
    token = CartService.generate_confirmation_token(
        tenant_id=tenant.id,
        user_id=test_user.id,
        action="add_item",
        target_id=str(product_a.id),
        quantity=1,
        price_snapshot=Decimal("1000.00")
    )
    
    # Try to use it for product B
    resp = await client.post(
        f"/api/v1/cart/items?confirmation_token={token}",
        headers=test_auth_headers,
        json={"product_id": str(product_b.id), "quantity": 1}
    )
    assert resp.status_code == 400
    assert "Token target mismatch" in resp.json()["detail"]
    
    # Try to use it for quantity 10
    resp = await client.post(
        f"/api/v1/cart/items?confirmation_token={token}",
        headers=test_auth_headers,
        json={"product_id": str(product_a.id), "quantity": 10}
    )
    assert resp.status_code == 400
    assert "Token quantity mismatch" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cart_validation_endpoint(client: AsyncClient, test_auth_headers, setup_cart_data, db: AsyncSession):
    product_a = setup_cart_data["product_a"]
    
    # Add item
    resp = await client.post("/api/v1/cart/items", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    token = resp.json()["detail"]["confirmation_token"]
    await client.post(f"/api/v1/cart/items?confirmation_token={token}", headers=test_auth_headers, json={"product_id": str(product_a.id), "quantity": 1})
    
    # Initially valid
    resp = await client.get("/api/v1/cart/validate", headers=test_auth_headers)
    assert resp.status_code == 200, resp.json()
    assert resp.json()["valid"] is True
    
    # Change price
    product_a.base_price = Decimal("1500.00")
    db.add(product_a)
    await db.commit()
    
    # Revalidate
    resp = await client.get("/api/v1/cart/validate", headers=test_auth_headers)
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["valid"] is False
    assert len(data["issues"]) == 1
    assert data["issues"][0]["type"] == "PRICE_CHANGED"
