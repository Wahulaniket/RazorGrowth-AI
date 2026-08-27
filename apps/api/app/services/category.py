"""
Category service.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:

    @staticmethod
    async def create(
        db: AsyncSession,
        tenant_id: UUID,
        data: CategoryCreate,
    ):
        existing = await CategoryRepository.get_by_slug(db, tenant_id, data.slug)
        if existing:
            raise ConflictError(message="Category slug already exists for this tenant.")

        if data.parent_id:
            parent = await CategoryRepository.get_by_id(db, data.parent_id)
            if not parent or parent.tenant_id != tenant_id:
                raise NotFoundError(resource="Parent category")

        return await CategoryRepository.create(
            db,
            tenant_id=tenant_id,
            name=data.name,
            slug=data.slug,
            description=data.description,
            parent_id=data.parent_id,
        )

    @staticmethod
    async def get(
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID,
    ):
        category = await CategoryRepository.get_by_id(db, category_id)
        if not category or category.tenant_id != tenant_id:
            raise NotFoundError(resource="Category")
        return category

    @staticmethod
    async def list(
        db: AsyncSession,
        tenant_id: UUID,
        parent_id: UUID | None = None,
    ):
        return await CategoryRepository.list_by_tenant(db, tenant_id, parent_id)

    @staticmethod
    async def update(
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID,
        data: CategoryUpdate,
    ):
        category = await CategoryRepository.get_by_id(db, category_id)
        if not category or category.tenant_id != tenant_id:
            raise NotFoundError(resource="Category")

        if data.slug and data.slug != category.slug:
            existing = await CategoryRepository.get_by_slug(db, tenant_id, data.slug)
            if existing:
                raise ConflictError(message="Category slug already exists for this tenant.")

        update_data = data.model_dump(exclude_unset=True)
        return await CategoryRepository.update(db, category, **update_data)
