from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate


class TenantRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        tenant_id: UUID,
    ) -> Tenant | None:
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> Tenant | None:
        result = await db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        data: TenantCreate,
    ) -> Tenant:

        tenant = Tenant(
            name=data.name,
            slug=data.slug,
            default_currency=data.default_currency.upper(),
            timezone=data.timezone,
        )

        db.add(tenant)

        await db.commit()
        await db.refresh(tenant)

        return tenant