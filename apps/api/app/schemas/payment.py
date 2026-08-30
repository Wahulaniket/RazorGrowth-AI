from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


from decimal import Decimal

class PaymentBase(BaseModel):
    amount: Decimal
    currency: str
    status: str


class PaymentCreate(BaseModel):
    order_id: UUID


class PaymentResponse(PaymentBase):
    id: UUID
    tenant_id: UUID
    order_id: UUID
    razorpay_order_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
