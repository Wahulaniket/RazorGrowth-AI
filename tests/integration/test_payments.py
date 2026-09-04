import uuid
import hmac
import hashlib
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role, Permission, RolePermission
from app.models.tenant_membership import TenantMembership
from app.models.checkout import Order
from app.models.payment import Payment

@pytest.fixture
async def payment_auth_headers(db: AsyncSession, tenant: Tenant, test_user: User):
    role = await db.scalar(select(Role).where(Role.name == "CheckoutAdmin"))
    if not role:
        role = Role(name="CheckoutAdmin")
        db.add(role)
        await db.flush()
        
        perms = {}
        for p_name in ["checkout.read", "checkout.write"]:
            p = await db.scalar(select(Permission).where(Permission.name == p_name))
            if not p:
                p = Permission(name=p_name)
                db.add(p)
                await db.flush()
            perms[p_name] = p
            
        for p_obj in perms.values():
            rp = await db.scalar(select(RolePermission).where(RolePermission.role_id == role.id, RolePermission.permission_id == p_obj.id))
            if not rp:
                db.add(RolePermission(role_id=role.id, permission_id=p_obj.id))
        await db.flush()
        
    mem = TenantMembership(user_id=test_user.id, tenant_id=tenant.id, role_id=role.id)
    db.add(mem)
    await db.flush()
    await db.refresh(test_user)
    
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
async def test_create_and_get_payment(client: AsyncClient, payment_auth_headers, db: AsyncSession, tenant: Tenant):
    # Setup order
    order = Order(
        tenant_id=tenant.id,
        currency="INR",
        subtotal=100.0,
        tax_total=18.0,
        total=118.0,
        status="CREATED"
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # Create Payment
    res = await client.post(
        "/api/v1/payments",
        headers=payment_auth_headers,
        json={"order_id": str(order.id)}
    )
    assert res.status_code == 201
    data = res.json()
    assert float(data["amount"]) == 118.0
    assert data["order_id"] == str(order.id)
    assert "razorpay_order_id" in data
    payment_id = data["id"]
    
    # Get Payment
    res = await client.get(f"/api/v1/payments/{payment_id}", headers=payment_auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == payment_id

@pytest.mark.asyncio
async def test_razorpay_webhook_signature_bypass(client: AsyncClient, db: AsyncSession, tenant: Tenant):
    # Setup order and payment
    order = Order(
        tenant_id=tenant.id,
        currency="INR",
        subtotal=200.0,
        tax_total=36.0,
        total=236.0,
        status="PENDING_PAYMENT"
    )
    db.add(order)
    await db.flush()
    
    payment = Payment(
        tenant_id=tenant.id,
        order_id=order.id,
        amount=236.0,
        currency="INR",
        status="CREATED",
        razorpay_order_id="order_test_123"
    )
    db.add(payment)
    await db.commit()
    
    # Send Webhook
    payload = {
        "id": "evt_test_123",
        "event": "payment.captured",
        "test_bypass_signature": True,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_456",
                    "order_id": "order_test_123",
                    "amount": 23600
                }
            }
        }
    }
    
    # The webhook needs a signature, but we bypass validation if `test_bypass_signature` is true.
    # However we still need to send SOME signature to pass the first check `if not signature`
    res = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"x-razorpay-signature": "dummy_signature"},
        json=payload
    )
    assert res.status_code == 200
    
    await db.refresh(payment)
    assert payment.status == "PAID"
    await db.refresh(order)
    # Test Duplicate Webhook
    res_dup = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"x-razorpay-signature": "dummy_signature"},
        json=payload
    )
    assert res_dup.status_code == 200
    assert "Already processed" in res_dup.json().get("message", "")

@pytest.mark.asyncio
async def test_razorpay_webhook_mismatch(client: AsyncClient, db: AsyncSession, tenant: Tenant):
    # Setup order and payment
    order = Order(
        tenant_id=tenant.id,
        currency="INR",
        subtotal=200.0,
        tax_total=36.0,
        total=236.0,
        status="PENDING_PAYMENT"
    )
    db.add(order)
    await db.flush()
    
    payment = Payment(
        tenant_id=tenant.id,
        order_id=order.id,
        amount=236.0,
        currency="INR",
        status="CREATED",
        razorpay_order_id="order_mismatch_123"
    )
    db.add(payment)
    await db.commit()
    
    # Send Webhook with mismatch amount
    payload = {
        "id": "evt_mismatch_123",
        "event": "payment.captured",
        "test_bypass_signature": True,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_456",
                    "order_id": "order_mismatch_123",
                    "amount": 10000, # Should be 23600
                    "currency": "INR"
                }
            }
        }
    }
    
    res = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"x-razorpay-signature": "dummy_signature"},
        json=payload
    )
    assert res.status_code == 400
    assert "Amount mismatch" in res.json().get("detail", "")
    
    # Send Webhook with mismatch currency
    payload["id"] = "evt_mismatch_124"
    payload["payload"]["payment"]["entity"]["amount"] = 23600
    payload["payload"]["payment"]["entity"]["currency"] = "USD"
    
    res2 = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"x-razorpay-signature": "dummy_signature"},
        json=payload
    )
    assert res2.status_code == 400
    assert "Currency mismatch" in res2.json().get("detail", "")

@pytest.mark.asyncio
async def test_razorpay_webhook_invalid_state_transition(client: AsyncClient, db: AsyncSession, tenant: Tenant):
    order = Order(
        tenant_id=tenant.id,
        currency="INR",
        subtotal=100.0,
        tax_total=18.0,
        total=118.0,
        status="PAYMENT_FAILED"
    )
    db.add(order)
    await db.flush()
    
    payment = Payment(
        tenant_id=tenant.id,
        order_id=order.id,
        amount=118.0,
        currency="INR",
        status="FAILED", # Already failed
        razorpay_order_id="order_failed_123"
    )
    db.add(payment)
    await db.commit()
    
    payload = {
        "id": "evt_late_capture_123",
        "event": "payment.captured",
        "test_bypass_signature": True,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_late",
                    "order_id": "order_failed_123",
                    "amount": 11800,
                    "currency": "INR"
                }
            }
        }
    }
    
    res = await client.post(
        "/api/v1/webhooks/razorpay",
        headers={"x-razorpay-signature": "dummy_signature"},
        json=payload
    )
    assert res.status_code == 200 # Webhook processed ok, but state wasn't updated
    
    await db.refresh(payment)
    assert payment.status == "FAILED" # State should not change to PAID
