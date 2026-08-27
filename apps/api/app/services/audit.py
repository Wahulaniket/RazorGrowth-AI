from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        details: Dict[str, Any],
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        api_key_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Records an audit log entry.
        """
        # If tenant_id isn't explicitly provided, attempt to extract it from session info
        if not tenant_id and db.info.get("tenant_id"):
            tenant_id = UUID(db.info["tenant_id"])
            
        # If api_key_id isn't explicitly provided, attempt to extract it from session info
        if not api_key_id and db.info.get("api_key_id"):
            api_key_id = UUID(db.info["api_key_id"])

        log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            api_key_id=api_key_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
        db.add(log)
        
        # Flush to generate ID, but caller is responsible for the transaction commit
        await db.flush()
        return log
