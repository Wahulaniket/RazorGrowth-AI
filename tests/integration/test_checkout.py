import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cart import Cart
from app.models.checkout import CheckoutQuote, Order
from app.core.security import create_access_token
from app.models.tenant_membership import TenantMembership
from app.models.role import Role

@pytest.fixture
def test_auth_headers(test_user, tenant):
    token = create_access_token(data={"sub": str(test_user.id), "tenant_id": str(tenant.id)})
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant.id)}

@pytest.fixture
async def setup_cart_with_items(db: AsyncSession, tenant, test_user, client: AsyncClient, test_auth_headers):
    from app.models.product import Product
    from app.models.category import Category
    from app.services.cart_service import CartService
    from app.schemas.cart import CartItemCreate
    from sqlalchemy import select

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

    category = Category(tenant_id=tenant.id, name="Checkout Cat", slug="checkout-cat")
    db.add(category)
    await db.flush()
    
    product = Product(
        tenant_id=tenant.id,
        category_id=category.id,
        name="Checkout Product",
        slug="checkout-product",
        sku="checkout-sku",
        base_price=Decimal("150.00"),
        status="ACTIVE"
    )
    db.add(product)
    await db.flush()
    
    # Add inventory
    from app.models.inventory import Inventory
    inv = Inventory(tenant_id=tenant.id, product_id=product.id, available_quantity=100)
    db.add(inv)
    await db.flush()

    cart = await CartService.get_or_create_cart(db, tenant.id, test_user.id)
    
    # Use CartService.add_item to avoid caching issues and MissingGreenlet
    try:
        await CartService.add_item(
            db=db,
            tenant_id=tenant.id,
            user_id=test_user.id,
            item_data=CartItemCreate(product_id=product.id, quantity=2)
        )
    except Exception as e:
        # Assuming CartConfirmationRequired
        if hasattr(e, "confirmation"):
            token = e.confirmation.confirmation_token
            await CartService.add_item(
                db=db,
                tenant_id=tenant.id,
                user_id=test_user.id,
                item_data=CartItemCreate(product_id=product.id, quantity=2),
                confirmation_token=token
            )
    await db.commit()
    
    # Reload cart fully
    cart = await CartService.get_or_create_cart(db, tenant.id, test_user.id)
    print(f"CART ITEMS LENGTH IN FIXTURE: {len(cart.items)}")
    return cart

@pytest.mark.asyncio
async def test_checkout_quote_create(client: AsyncClient, test_auth_headers, setup_cart_with_items):
    cart = setup_cart_with_items
    
    res = await client.post(
        "/api/v1/checkout/quote",
        headers=test_auth_headers,
        json={"cart_id": str(cart.id)}
    )
    
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["subtotal"] == "300.00"
    assert data["total"] == "354.0000"
    assert data["cart_id"] == str(cart.id)
    assert data["status"] == "ACTIVE"

@pytest.mark.asyncio
async def test_checkout_quote_confirm(client: AsyncClient, test_auth_headers, setup_cart_with_items, db: AsyncSession, tenant):
    cart = setup_cart_with_items
    
    # 1. Create quote
    res = await client.post(
        "/api/v1/checkout/quote",
        headers=test_auth_headers,
        json={"cart_id": str(cart.id)}
    )
    assert res.status_code == 200
    quote_id = res.json()["id"]
    
    # 2. Confirm quote
    res = await client.post(
        f"/api/v1/checkout/{quote_id}/confirm",
        headers=test_auth_headers,
        json={"confirmation_type": "USER_CONFIRMATION"}
    )
    
    assert res.status_code == 200
    order_data = res.json()
    assert order_data["status"] == "CREATED"
    assert order_data["payment_status"] == "UNPAID"
    assert len(order_data["items"]) == 1
    
    # Verify DB state
    order = await db.get(Order, order_data["id"])
    assert order is not None
    assert order.cart_id == cart.id
    
    # Verify cart is converted
    updated_cart = await db.get(Cart, cart.id)
    assert updated_cart.status == "CONVERTED"
