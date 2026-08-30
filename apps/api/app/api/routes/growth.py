import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_tenant_by_id, get_optional_user
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.growth import (
    RecommendationResponse,
    ExperimentParticipateRequest,
    ExperimentParticipateResponse,
    AnalyticsEventCreate,
    AnalyticsEventResponse
)
from app.services.growth_service import GrowthService

router = APIRouter(prefix="", tags=["growth"])

@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant_by_id),
    user: Optional[User] = Depends(get_optional_user),
):
    user_id = user.id if user else None
    recommendations = await GrowthService.get_recommendations(db, tenant.id, user_id)
    return recommendations

@router.post("/experiments/participate", response_model=ExperimentParticipateResponse)
async def participate_experiment(
    request: ExperimentParticipateRequest,
    x_session_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant_by_id),
    user: Optional[User] = Depends(get_optional_user),
):
    try:
        participant = await GrowthService.participate_in_experiment(
            db, 
            tenant.id, 
            request.experiment_name, 
            user.id if user else None,
            x_session_id
        )
        await db.commit()
        return participant
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analytics/events", response_model=AnalyticsEventResponse, status_code=201)
async def track_event(
    request: AnalyticsEventCreate,
    x_session_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant_by_id),
    user: Optional[User] = Depends(get_optional_user),
):
    event = await GrowthService.track_event(
        db,
        tenant.id,
        request.event_type,
        request.payload,
        user.id if user else None,
        x_session_id
    )
    await db.commit()
    return event
