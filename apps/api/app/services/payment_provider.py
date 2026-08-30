import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import razorpay

from app.core.config import get_settings

class PaymentProvider(ABC):
    @abstractmethod
    async def create_order(self, amount: float, currency: str, receipt_id: str) -> Dict[str, Any]:
        """
        Create a payment order with the provider.
        amount should be the canonical amount (e.g., total in major currency units like INR, provider handles paise if needed).
        """
        pass
    
    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the signature of an incoming webhook event.
        """
        pass

class FakePaymentProvider(PaymentProvider):
    async def create_order(self, amount: float, currency: str, receipt_id: str) -> Dict[str, Any]:
        # Mock behavior for local testing and CI
        return {
            "id": f"order_fake_{uuid.uuid4().hex[:14]}",
            "amount": int(amount * 100),
            "currency": currency,
            "receipt": receipt_id,
            "status": "created"
        }
        
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        # In fake mode, we might just accept it or implement a dummy verification
        # Usually webhooks in fake mode bypass this if test_bypass_signature=True
        return True


class RazorpayPaymentProvider(PaymentProvider):
    def __init__(self):
        settings = get_settings()
        self.client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        self.webhook_secret = settings.razorpay_webhook_secret

    async def create_order(self, amount: float, currency: str, receipt_id: str) -> Dict[str, Any]:
        # Razorpay expects amount in subunits (paise for INR)
        # So we multiply the major unit float by 100
        amount_in_subunits = int(round(amount * 100))
        
        data = {
            "amount": amount_in_subunits,
            "currency": currency,
            "receipt": receipt_id,
            "payment_capture": 1 # Auto capture
        }
        
        import asyncio
        loop = asyncio.get_running_loop()
        order = await loop.run_in_executor(None, lambda: self.client.order.create(data=data))
        return order

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        try:
            self.client.utility.verify_webhook_signature(
                payload.decode('utf-8'),
                signature,
                self.webhook_secret
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            return False


def get_payment_provider() -> PaymentProvider:
    settings = get_settings()
    if settings.payment_provider == "razorpay":
        return RazorpayPaymentProvider()
    return FakePaymentProvider()
