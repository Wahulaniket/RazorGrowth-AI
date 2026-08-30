from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PolicyRule(BaseModel):
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    max_discount_percent: Optional[float] = None
    allowed_categories: Optional[List[str]] = None
    require_confirmation: Optional[bool] = None

class PolicyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    policy_type: str = Field(..., max_length=50)
    level: str = Field("MERCHANT", max_length=50)
    rules: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class PolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    policy_type: Optional[str] = Field(None, max_length=50)
    level: Optional[str] = Field(None, max_length=50)
    rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class PolicyResponse(PolicyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID

class PolicyEvaluationRequest(BaseModel):
    action: str
    context: Dict[str, Any] = Field(default_factory=dict)

class PolicyDecision(BaseModel):
    decision: Literal["ALLOW", "DENY"]
    reasons: List[str]
