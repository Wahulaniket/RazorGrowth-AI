from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey


class ApiKeyRepository:
    @staticmethod
    async def get_by_id_for_tenant(
        db: AsyncSession, tenant_id: UUID, key_id: UUID
    ) -> ApiKey | None:
        """
        Retrieves an API key by ID, ensuring it belongs to the specified tenant.
        """
        stmt = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_for_tenant(
        db: AsyncSession, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ApiKey]:
        """
        Lists all API keys for a tenant.
        """
        stmt = (
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant_id)
            .order_by(ApiKey.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, api_key: ApiKey) -> ApiKey:
        db.add(api_key)
        await db.flush()
        return api_key

    @staticmethod
    async def update(db: AsyncSession, api_key: ApiKey) -> ApiKey:
        await db.flush()
        return api_key
