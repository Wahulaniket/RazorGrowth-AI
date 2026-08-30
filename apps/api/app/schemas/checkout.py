from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class CheckoutQuoteRequest(BaseModel):
    cart_id: UUID

class CheckoutQuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    cart_id: UUID
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    expires_at: datetime
    status: str
    created_at: datetime

class CheckoutConfirmRequest(BaseModel):
    confirmation_type: str = Field(..., description="E.g., USER_CONFIRMATION, AGENT_APPROVAL")
    session_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    line_total: Decimal
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_")

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    customer_id: Optional[UUID] = None
    cart_id: Optional[UUID] = None
    external_order_id: Optional[str] = None
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    status: str
    payment_status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
