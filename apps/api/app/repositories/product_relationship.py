"""
ProductRelationship repository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_relationship import ProductRelationship


class ProductRelationshipRepository:

    @staticmethod
    async def get_by_product(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        relationship_type: str | None = None,
    ) -> list[ProductRelationship]:
        query = select(ProductRelationship).where(
            ProductRelationship.tenant_id == tenant_id,
            ProductRelationship.source_product_id == product_id,
        )
        if relationship_type:
            query = query.where(
                ProductRelationship.relationship_type == relationship_type
            )
        query = query.order_by(ProductRelationship.score.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        tenant_id: UUID,
        source_product_id: UUID,
        target_product_id: UUID,
        relationship_type: str,
        score: float = 0.5,
        metadata: dict | None = None,
    ) -> ProductRelationship:
        rel = ProductRelationship(
            tenant_id=tenant_id,
            source_product_id=source_product_id,
            target_product_id=target_product_id,
            relationship_type=relationship_type,
            score=score,
            metadata_=metadata or {},
        )
        db.add(rel)
        await db.commit()
        await db.refresh(rel)
        return rel
