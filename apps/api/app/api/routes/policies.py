from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_current_tenant, get_current_user, require_permission
from app.core.permissions import PermissionEnum
from app.db.session import get_db
from app.models.policy import Policy
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.policy import PolicyCreate, PolicyDecision, PolicyEvaluationRequest, PolicyResponse, PolicyUpdate
from app.services.policy_engine import PolicyEngineService
from app.services.audit import AuditService

router = APIRouter()

@router.get("", response_model=List[PolicyResponse])
async def list_policies(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionEnum.POLICIES_READ)),
):
    tenant_id = tenant.id
    policies = await PolicyEngineService.get_policies(db, tenant_id)
    return policies

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_in: PolicyCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionEnum.POLICIES_WRITE)),
):
    tenant_id = tenant.id
    policy = await PolicyEngineService.create_policy(db, tenant_id, policy_in)
    
    await AuditService.log_event(
        db=db,
        tenant_id=tenant_id,
        action="POLICY_CREATED",
        user_id=user.id,
        entity_id=policy.id,
        entity_type="POLICY",
        details={"name": policy.name, "policy_type": policy.policy_type}
    )
    
    await db.commit()
    return policy

@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    policy_update: PolicyUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionEnum.POLICIES_WRITE)),
):
    tenant_id = tenant.id
    policy = await db.get(Policy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = policy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    await AuditService.log_event(
        db=db,
        tenant_id=tenant_id,
        action="POLICY_UPDATED",
        user_id=user.id,
        entity_id=policy.id,
        entity_type="POLICY",
        details={"updated_fields": list(update_data.keys())}
    )

    await db.commit()
    return policy

@router.post("/internal/evaluate", response_model=PolicyDecision)
async def evaluate_policy(
    eval_req: PolicyEvaluationRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(require_permission(PermissionEnum.AGENT_USE)),
):
    """
    Evaluates policy for a given action.
    This is an internal API that mimics the internal policy evaluation.
    We require agent.use permission to simulate the agent evaluation process.
    """
    tenant_id = tenant.id
    context = eval_req.model_dump()
    
    decision = await PolicyEngineService.evaluate(db, tenant_id, eval_req.action, context)
    
    event_type = "POLICY_EVALUATED" if decision.decision == "ALLOW" else "POLICY_BLOCKED"
    await AuditService.log_event(
        db=db,
        tenant_id=tenant_id,
        action=event_type,
        user_id=user.id,
        entity_id=None,
        entity_type="POLICY_EVALUATION",
        details={"action": eval_req.action, "decision": decision.decision, "reasons": decision.reasons}
    )
    
    await db.commit()
    return decision
