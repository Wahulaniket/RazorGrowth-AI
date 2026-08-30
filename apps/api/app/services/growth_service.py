import uuid
import random
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth import Recommendation, Experiment, ExperimentParticipant, AnalyticsEvent

class GrowthService:
    @staticmethod
    async def get_recommendations(
        db: AsyncSession, tenant_id: uuid.UUID, user_id: Optional[uuid.UUID]
    ) -> List[Recommendation]:
        # For simplicity, fetch top recommendations for the user or generic ones
        stmt = select(Recommendation).where(Recommendation.tenant_id == tenant_id)
        if user_id:
            # Maybe filter by user_id OR user_id == null
            stmt = stmt.where(
                (Recommendation.user_id == user_id) | (Recommendation.user_id.is_(None))
            )
        else:
            stmt = stmt.where(Recommendation.user_id.is_(None))
            
        stmt = stmt.order_by(Recommendation.score.desc()).limit(10)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def participate_in_experiment(
        db: AsyncSession, tenant_id: uuid.UUID, experiment_name: str, user_id: Optional[uuid.UUID], session_id: Optional[str]
    ) -> ExperimentParticipant:
        # Find experiment
        result = await db.execute(
            select(Experiment).where(
                Experiment.tenant_id == tenant_id,
                Experiment.name == experiment_name,
                Experiment.status == "ACTIVE"
            )
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise ValueError("Experiment not found or inactive")
            
        # Check if already participating
        stmt = select(ExperimentParticipant).where(
            ExperimentParticipant.experiment_id == experiment.id,
            ExperimentParticipant.tenant_id == tenant_id
        )
        if user_id:
            stmt = stmt.where(ExperimentParticipant.user_id == user_id)
        elif session_id:
            stmt = stmt.where(ExperimentParticipant.session_id == session_id)
        else:
            raise ValueError("Must provide either user_id or session_id")
            
        existing = await db.execute(stmt)
        participant = existing.scalar_one_or_none()
        
        if participant:
            return participant
            
        # Assign variant randomly based on weights if provided, or equal distribution
        variants = experiment.variants
        variant_names = list(variants.keys()) if variants else ["control", "treatment"]
        assigned = random.choice(variant_names)
        
        participant = ExperimentParticipant(
            tenant_id=tenant_id,
            experiment_id=experiment.id,
            user_id=user_id,
            session_id=session_id,
            variant=assigned
        )
        db.add(participant)
        await db.flush()
        
        return participant

    @staticmethod
    async def track_event(
        db: AsyncSession, tenant_id: uuid.UUID, event_type: str, payload: dict, user_id: Optional[uuid.UUID], session_id: Optional[str]
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            payload=payload
        )
        db.add(event)
        await db.flush()
        return event

