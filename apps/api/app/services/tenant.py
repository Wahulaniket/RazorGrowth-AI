from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.tenant import TenantRepository
from app.schemas.tenant import TenantCreate


class TenantService:

    @staticmethod
    async def create(
        db: AsyncSession,
        data: TenantCreate,
    ):
        existing = await TenantRepository.get_by_slug(
            db,
            data.slug,
        )

        if existing:
            raise ConflictError(message="Tenant slug already exists.")

        return await TenantRepository.create(
            db,
            data=data,
        )

    @staticmethod
    async def get(
        db: AsyncSession,
        tenant_id: UUID,
    ):
        tenant = await TenantRepository.get_by_id(
            db,
            tenant_id,
        )

        if not tenant:
            raise NotFoundError(resource="Tenant")

        return tenant