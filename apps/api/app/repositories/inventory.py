"""
Inventory repository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory


class InventoryRepository:

    @staticmethod
    async def get_by_product(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID | None = None,
    ) -> Inventory | None:
        query = select(Inventory).where(
            Inventory.tenant_id == tenant_id,
            Inventory.product_id == product_id,
        )
        if variant_id is not None:
            query = query.where(Inventory.variant_id == variant_id)
        else:
            query = query.where(Inventory.variant_id.is_(None))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        available_quantity: int,
        reserved_quantity: int = 0,
        variant_id: UUID | None = None,
    ) -> Inventory:
        """Create or update an inventory record."""
        existing = await InventoryRepository.get_by_product(
            db, tenant_id, product_id, variant_id,
        )
        if existing:
            existing.available_quantity = available_quantity
            existing.reserved_quantity = reserved_quantity
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            inv = Inventory(
                tenant_id=tenant_id,
                product_id=product_id,
                variant_id=variant_id,
                available_quantity=available_quantity,
                reserved_quantity=reserved_quantity,
            )
            db.add(inv)
            await db.commit()
            await db.refresh(inv)
            return inv
