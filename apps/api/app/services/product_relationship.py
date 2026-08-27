"""
ProductRelationship service.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.product_relationship import RELATIONSHIP_TYPES
from app.repositories.product import ProductRepository
from app.repositories.product_relationship import ProductRelationshipRepository
from app.schemas.product_relationship import RelationshipCreate


class ProductRelationshipService:

    @staticmethod
    async def create(
        db: AsyncSession,
        tenant_id: UUID,
        source_product_id: UUID,
        data: RelationshipCreate,
    ):
        # Validate source product
        source = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, source_product_id,
        )
        if not source:
            raise NotFoundError(resource="Source product")

        # Validate target product
        target = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, data.target_product_id,
        )
        if not target:
            raise NotFoundError(resource="Target product")

        # Prevent self-referencing
        if source_product_id == data.target_product_id:
            raise ValidationError(message="A product cannot have a relationship with itself.")

        return await ProductRelationshipRepository.create(
            db,
            tenant_id=tenant_id,
            source_product_id=source_product_id,
            target_product_id=data.target_product_id,
            relationship_type=data.relationship_type,
            score=float(data.score),
            metadata=data.metadata,
        )

    @staticmethod
    async def list(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        relationship_type: str | None = None,
    ):
        # Validate product exists
        product = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, product_id,
        )
        if not product:
            raise NotFoundError(resource="Product")

        return await ProductRelationshipRepository.get_by_product(
            db, tenant_id, product_id, relationship_type,
        )
