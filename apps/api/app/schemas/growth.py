import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    score: float
    reason: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class ExperimentParticipateRequest(BaseModel):
    experiment_name: str


class ExperimentParticipateResponse(BaseModel):
    experiment_id: uuid.UUID
    variant: str
    
    model_config = ConfigDict(from_attributes=True)


class AnalyticsEventCreate(BaseModel):
    event_type: str
    payload: Dict[str, Any]

class AnalyticsEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    
    model_config = ConfigDict(from_attributes=True)
