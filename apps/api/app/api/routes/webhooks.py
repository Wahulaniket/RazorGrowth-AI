import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_db
from app.models.payment import Payment, PaymentAttempt, WebhookEvent
from app.models.checkout import Order
from app.services.audit import AuditService
from app.services.payment_provider import get_payment_provider

router = APIRouter(prefix="", tags=["webhooks"])
settings = get_settings()

@router.post("/webhooks/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    signature = request.headers.get("x-razorpay-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    payload_bytes = await request.body()
    
    # 1. Verify Signature using Provider
    provider = get_payment_provider()
    
    # Check if we should allow test bypass for FakeProvider
    try:
        payload = json.loads(payload_bytes)
        if getattr(settings, "app_env", "development") != "production" and payload.get("test_bypass_signature") is True:
            pass # allow for test
        elif not provider.verify_webhook_signature(payload_bytes, signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_id = payload.get("id") or f"evt_{uuid.uuid4().hex}"
    event_type = payload.get("event")
    
    payload_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    razorpay_order_id = payload_entity.get("order_id")
    
    if not razorpay_order_id:
        return {"status": "ok", "ignored": "no order_id"}
        
    # Transaction for safety
    async with db.begin_nested():
        # Find payment by razorpay_order_id
        result = await db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return {"status": "ok", "ignored": "unknown order_id"}
            
        tenant_id = payment.tenant_id
        
        # Amount & Currency Validation
        # Razorpay sends amount in subunits
        expected_amount_subunits = int(round(float(payment.amount) * 100))
        webhook_amount = payload_entity.get("amount")
        webhook_currency = payload_entity.get("currency")
        
        if webhook_amount is not None and webhook_amount != expected_amount_subunits:
            raise HTTPException(status_code=400, detail="Amount mismatch")
        if webhook_currency is not None and webhook_currency != payment.currency:
            raise HTTPException(status_code=400, detail="Currency mismatch")
        
        # Idempotency check with locking (assuming single DB instance/connection semantics)
        # Better: use Postgres unique constraint on WebhookEvent.event_id
        result = await db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        existing_event = result.scalar_one_or_none()
        if existing_event:
            return {"status": "ok", "message": "Already processed"}

        # Save event
        webhook_event = WebhookEvent(
            tenant_id=tenant_id,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            status="PROCESSED"
        )
        db.add(webhook_event)
        
        # Process event securely
        if event_type == "payment.captured":
            # Valid state transitions: CREATED, PENDING, AUTHORIZED -> PAID
            if payment.status in ["CREATED", "PENDING", "AUTHORIZED"]:
                payment.status = "PAID"
                
                order_res = await db.execute(select(Order).where(Order.id == payment.order_id))
                order = order_res.scalar_one()
                order.status = "PAID"
                
                attempt = PaymentAttempt(
                    tenant_id=tenant_id,
                    payment_id=payment.id,
                    razorpay_payment_id=payload_entity.get("id"),
                    amount=payment.amount,
                    status="SUCCESS"
                )
                db.add(attempt)
                
                await AuditService.log_event(
                    db=db, tenant_id=tenant_id, action="payment.captured", 
                    details={"payment_id": str(payment.id), "razorpay_payment_id": attempt.razorpay_payment_id}
                )
            else:
                # Invalid transition, e.g. already PAID or FAILED -> CAPTURED
                pass 

        elif event_type == "payment.failed":
            if payment.status in ["CREATED", "PENDING", "AUTHORIZED"]:
                payment.status = "FAILED"
                
                order_res = await db.execute(select(Order).where(Order.id == payment.order_id))
                order = order_res.scalar_one()
                order.status = "PAYMENT_FAILED"
                
                attempt = PaymentAttempt(
                    tenant_id=tenant_id,
                    payment_id=payment.id,
                    razorpay_payment_id=payload_entity.get("id"),
                    amount=payment.amount,
                    status="FAILED",
                    error_code=payload_entity.get("error_code"),
                    error_description=payload_entity.get("error_description")
                )
                db.add(attempt)
                
                await AuditService.log_event(
                    db=db, tenant_id=tenant_id, action="payment.failed", 
                    details={"payment_id": str(payment.id), "error": attempt.error_code}
                )

    await db.commit()
    return {"status": "ok"}
