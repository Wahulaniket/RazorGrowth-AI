from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyDecision, PolicyEvaluationRequest, PolicyUpdate
from app.services.audit import AuditService


class PolicyEngineService:
    @staticmethod
    async def get_policies(db: AsyncSession, tenant_id: UUID) -> List[Policy]:
        """Fetch all active policies for a tenant."""
        result = await db.execute(
            select(Policy)
            .where(Policy.tenant_id == tenant_id, Policy.is_active == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_policy(db: AsyncSession, tenant_id: UUID, policy_in: PolicyCreate) -> Policy:
        policy = Policy(
            tenant_id=tenant_id,
            name=policy_in.name,
            policy_type=policy_in.policy_type,
            level=policy_in.level,
            rules=policy_in.rules,
            is_active=policy_in.is_active,
        )
        db.add(policy)
        await db.flush()
        return policy

    @staticmethod
    async def update_policy(db: AsyncSession, tenant_id: UUID, policy_id: UUID, policy_in: PolicyUpdate) -> Policy:
        result = await db.execute(
            select(Policy).where(Policy.id == policy_id, Policy.tenant_id == tenant_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise ValueError("Policy not found")

        update_data = policy_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
            
        await db.flush()
        return policy

    @staticmethod
    async def evaluate(db: AsyncSession, tenant_id: UUID, action: str, context: dict) -> PolicyDecision:
        """
        Evaluate an action deterministically against all active policies.
        Fail closed (DENY) if any policy is violated.
        """
        try:
            policies = await PolicyEngineService.get_policies(db, tenant_id)
        except Exception:
            return PolicyDecision(decision="DENY", reasons=["INTERNAL_ERROR"])

        if not policies:
            # If no policies exist, we should probably allow safe actions, but for financial actions,
            # we might want to default to block. However, if no rules exist, there's nothing to violate.
            # We will allow it, assuming base RBAC already authorized the action invocation.
            pass

        reasons = []
        for policy in policies:
            # Evaluate TRANSACTION_LIMIT
            if policy.policy_type == "TRANSACTION_LIMIT" and action == "PAYMENT":
                max_amount = policy.rules.get("max_amount")
                amount = context.get("amount")
                if max_amount is not None:
                    if amount is None:
                        return PolicyDecision(decision="DENY", reasons=["MISSING_AMOUNT_CONTEXT"])
                    if amount > max_amount:
                        decision = PolicyDecision(decision="DENY", reasons=[f"EXCEEDS_MAX_AMOUNT ({policy.name})"])
                        await AuditService.log_event(db, "policy.blocked", {"action": action, "reasons": decision.reasons, "context": context}, tenant_id)
                        return decision

            # Evaluate CONFIRMATION_REQUIREMENT
            if policy.policy_type == "CONFIRMATION_REQUIREMENT" and action == "PAYMENT":
                require_confirmation = policy.rules.get("require_confirmation", True)
                if require_confirmation:
                    confirmed = context.get("customer_confirmed")
                    if not confirmed:
                        decision = PolicyDecision(decision="DENY", reasons=[f"CUSTOMER_CONFIRMATION_REQUIRED ({policy.name})"])
                        await AuditService.log_event(db, "policy.blocked", {"action": action, "reasons": decision.reasons, "context": context}, tenant_id)
                        return decision

            # Evaluate DISCOUNT_LIMIT
            if policy.policy_type == "DISCOUNT_LIMIT" and action in ("DISCOUNT", "PAYMENT"):
                max_discount = policy.rules.get("max_discount_percent")
                applied_discount = context.get("discount_percent")
                if max_discount is not None and applied_discount is not None:
                    if applied_discount > max_discount:
                        decision = PolicyDecision(decision="DENY", reasons=[f"EXCEEDS_MAX_DISCOUNT ({policy.name})"])
                        await AuditService.log_event(db, "policy.blocked", {"action": action, "reasons": decision.reasons, "context": context}, tenant_id)
                        return decision

        if not reasons:
            reasons = ["ALL_POLICIES_PASSED"]
            
        return PolicyDecision(decision="ALLOW", reasons=reasons)
