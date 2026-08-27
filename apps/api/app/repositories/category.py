"""
Category repository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        category_id: UUID,
    ) -> Category | None:
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(
        db: AsyncSession,
        tenant_id: UUID,
        slug: str,
    ) -> Category | None:
        result = await db.execute(
            select(Category).where(
                Category.tenant_id == tenant_id,
                Category.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        parent_id: UUID | None = None,
    ) -> list[Category]:
        query = select(Category).where(Category.tenant_id == tenant_id)
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        else:
            query = query.where(Category.parent_id.is_(None))
        query = query.order_by(Category.name)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        tenant_id: UUID,
        name: str,
        slug: str,
        description: str | None = None,
        parent_id: UUID | None = None,
    ) -> Category:
        category = Category(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update(
        db: AsyncSession,
        category: Category,
        **kwargs,
    ) -> Category:
        for key, value in kwargs.items():
            if value is not None:
                setattr(category, key, value)
        await db.commit()
        await db.refresh(category)
        return category
