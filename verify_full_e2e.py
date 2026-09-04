import asyncio
import uuid
import httpx
from app.main import app

async def run_full_verification():
    print("=== STARTING FULL E2E INTEGRATION VERIFICATION ===")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=30.0) as client:
        # 1. AUTH - Register
        unique_email = f"e2e_customer_{uuid.uuid4().hex[:8]}@example.com"
        print(f"1. Registering user: {unique_email}")
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": unique_email,
            "password": "Password123!",
            "name": "E2E Verified User"
        })
        assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
        user_data = reg_res.json()
        print(f"   [PASS] User registered: {user_data['id']}")

        # 2. AUTH - Login
        print("2. Logging in...")
        login_res = await client.post("/api/v1/auth/login", json={
            "email": unique_email,
            "password": "Password123!"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        print(f"   [PASS] Login successful, token acquired")

        headers = {"Authorization": f"Bearer {token}"}
        # Create tenant, role, membership & seed product for test user via db
        from app.models.tenant import Tenant
        from app.models.tenant_membership import TenantMembership
        from app.models.role import Role
        from app.models.product import Product
        from app.db.session import get_db
        from scripts.bootstrap_rbac import bootstrap_rbac
        from sqlalchemy import select

        async for db in get_db():
            await bootstrap_rbac(db)

            # Check or create default tenant
            res = await db.execute(select(Tenant))
            tenant = res.scalars().first()
            if not tenant:
                tenant = Tenant(name="E2E Test Tenant", slug=f"e2e-tenant-{uuid.uuid4().hex[:6]}", default_currency="INR")
                db.add(tenant)
                await db.commit()
                await db.refresh(tenant)

            # Check or create Admin role
            role_res = await db.execute(select(Role))
            role = role_res.scalars().first()
            if not role:
                role = Role(name="Admin", description="Administrator")
                db.add(role)
                await db.commit()
                await db.refresh(role)

            # Add membership
            membership = TenantMembership(user_id=uuid.UUID(user_data["id"]), tenant_id=tenant.id, role_id=role.id)
            db.add(membership)

            # Create test category & product for tenant
            from app.models.category import Category
            cat_res = await db.execute(select(Category))
            category = cat_res.scalars().first()
            if not category:
                category = Category(
                    tenant_id=tenant.id,
                    name="Electronics",
                    slug=f"electronics-{uuid.uuid4().hex[:6]}"
                )
                db.add(category)
                await db.commit()
                await db.refresh(category)

            from app.models.inventory import Inventory
            product = Product(
                tenant_id=tenant.id,
                category_id=category.id,
                name="Wireless Headphones Pro",
                slug=f"headphones-pro-{uuid.uuid4().hex[:6]}",
                sku=f"SKU-HP-{uuid.uuid4().hex[:4]}",
                base_price=9999.00,
                currency="INR",
                status="ACTIVE"
            )
            db.add(product)
            await db.flush()

            inventory = Inventory(
                tenant_id=tenant.id,
                product_id=product.id,
                available_quantity=100,
                reserved_quantity=0
            )
            db.add(inventory)
            await db.commit()
            tenant_id = str(tenant.id)
            break

        print(f"   [PASS] Tenant ID resolved: {tenant_id}")
        headers["X-Tenant-ID"] = tenant_id

        # 3. AUTH - Me
        me_res = await client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200, f"Get me failed: {me_res.text}"
        print(f"   [PASS] GET /api/v1/auth/me verified")

        # 4. CATALOG - Search
        print("4. Searching catalog...")
        cat_res = await client.post("/api/v1/catalog/search", headers=headers, json={"limit": 10})
        assert cat_res.status_code == 200, f"Catalog search failed: {cat_res.text}"
        items = cat_res.json()["items"]
        assert len(items) > 0, "No products returned from catalog search"
        target_product_id = str(product.id)
        print(f"   [PASS] Target Product ID: {target_product_id}")

        # 5. CART - Get / Create Cart
        print("5. Getting cart...")
        cart_res = await client.get("/api/v1/cart/", headers=headers)
        assert cart_res.status_code == 200, f"Get cart failed: {cart_res.text}"
        cart = cart_res.json()
        cart_id = cart["id"]
        print(f"   [PASS] Active Cart ID: {cart_id}")

        # 6. CART - Add Item
        print("6. Adding item to cart...")
        add_res = await client.post("/api/v1/cart/items", headers=headers, json={
            "product_id": target_product_id,
            "quantity": 2
        })
        if add_res.status_code == 402:
            conf_token = add_res.json()["detail"]["confirmation_token"]
            print("   [POLICY ENGINE] Confirmation required for high-value item. Resending with confirmation_token...")
            add_res = await client.post(
                "/api/v1/cart/items",
                headers=headers,
                params={"confirmation_token": conf_token},
                json={
                    "product_id": target_product_id,
                    "quantity": 2
                }
            )

        assert add_res.status_code == 200, f"Add item failed: {add_res.text}"
        updated_cart = add_res.json()
        cart_id = updated_cart["id"]
        assert len(updated_cart["items"]) > 0
        item_id = updated_cart["items"][0]["id"]
        print(f"   [PASS] Item added to cart. Item ID: {item_id}, Cart ID: {cart_id}")

        # 7. CART - Validate
        print("7. Validating cart...")
        val_res = await client.get("/api/v1/cart/validate", headers=headers)
        assert val_res.status_code == 200, f"Validate cart failed: {val_res.text}"
        assert val_res.json()["valid"] is True
        print("   [PASS] Cart validation passed")

        # 8. CHECKOUT - Create Quote
        print("8. Creating checkout quote...")
        quote_res = await client.post("/api/v1/checkout/quote", headers=headers, json={
            "cart_id": cart_id
        })
        assert quote_res.status_code == 200, f"Quote creation failed: {quote_res.text}"
        quote = quote_res.json()
        quote_id = quote["id"]
        print(f"   [PASS] Checkout quote created: {quote_id}, Total: {quote['total']} {quote['currency']}")

        # 9. CHECKOUT - Confirm Quote -> Order
        print("9. Confirming quote...")
        confirm_res = await client.post(f"/api/v1/checkout/{quote_id}/confirm", headers=headers, json={
            "confirmation_type": "USER_CONFIRMATION"
        })
        assert confirm_res.status_code == 200, f"Confirm quote failed: {confirm_res.text}"
        order = confirm_res.json()
        order_id = order["id"]
        print(f"   [PASS] Quote confirmed. Order ID: {order_id}, Status: {order['status']}")

        # 10. PAYMENT - Process Fake Payment
        print("10. Processing fake payment...")
        pay_res = await client.post("/api/v1/payments", headers=headers, json={
            "order_id": order_id
        })
        assert pay_res.status_code == 201, f"Payment failed: {pay_res.text}"
        payment = pay_res.json()
        print(f"    [PASS] Payment processed: ID {payment['id']}, Status: {payment['status']}, Amount: {payment['amount']} {payment['currency']}")

        # 11. ORDERS - List & Detail
        print("11. Verifying Orders API...")
        orders_list_res = await client.get("/api/v1/orders/", headers=headers)
        assert orders_list_res.status_code == 200, f"List orders failed: {orders_list_res.text}"
        orders = orders_list_res.json()
        assert any(o["id"] == order_id for o in orders)
        
        order_detail_res = await client.get(f"/api/v1/orders/{order_id}", headers=headers)
        assert order_detail_res.status_code == 200
        assert order_detail_res.json()["payment_status"] in ["UNPAID", "COMPLETED", "PENDING"]
        print(f"   [PASS] Orders API verified with status: {order_detail_res.json()['status']}, payment_status: {order_detail_res.json()['payment_status']}")

        # 12. AI AGENT - Chat
        print("12. Testing AI Agent Chat (/api/v1/agent/chat)...")
        agent_res = await client.post("/api/v1/agent/chat", headers=headers, json={
            "message": "Find me wireless noise-cancelling headphones under ₹15,000"
        })
        assert agent_res.status_code == 200, f"Agent chat failed: {agent_res.text}"
        agent_data = agent_res.json()
        print(f"    [PASS] AI Agent responded. Message: {agent_data['message'][:60]}... Recommendations: {len(agent_data['recommendations'])}")

        # 13. POLICIES - List & Evaluate
        print("13. Testing Policy Engine...")
        pol_list_res = await client.get("/api/v1/policies", headers=headers)
        assert pol_list_res.status_code == 200, f"List policies failed: {pol_list_res.text}"
        print(f"    [PASS] List policies returned {len(pol_list_res.json())} rules")

        # 14. SECURITY - Unauthorized Rejection
        print("14. Verifying Security & Auth Rejections...")
        unauth_res = await client.get("/api/v1/cart/")
        assert unauth_res.status_code in (401, 403), f"Unauthenticated request should fail, got: {unauth_res.status_code}"
        print(f"    [PASS] Security correctly returned HTTP {unauth_res.status_code} for unauthenticated request")

    print("\n==================================================")
    print("ALL END-TO-END INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_full_verification())
