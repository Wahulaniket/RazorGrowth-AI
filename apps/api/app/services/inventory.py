"""
Inventory service.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.inventory import InventoryRepository
from app.repositories.product import ProductRepository
from app.schemas.inventory import InventoryUpdate


class InventoryService:

    @staticmethod
    async def get(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        variant_id: UUID | None = None,
    ):
        # Validate product exists and belongs to tenant
        product = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, product_id,
        )
        if not product:
            raise NotFoundError(resource="Product")

        inv = await InventoryRepository.get_by_product(
            db, tenant_id, product_id, variant_id,
        )
        if not inv:
            # Return a "zero stock" response rather than 404
            return {
                "product_id": product_id,
                "variant_id": variant_id,
                "available_quantity": 0,
                "reserved_quantity": 0,
                "in_stock": False,
            }
        return inv

    @staticmethod
    async def update(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        data: InventoryUpdate,
        variant_id: UUID | None = None,
    ):
        product = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, product_id,
        )
        if not product:
            raise NotFoundError(resource="Product")

        return await InventoryRepository.upsert(
            db,
            tenant_id=tenant_id,
            product_id=product_id,
            available_quantity=data.available_quantity,
            reserved_quantity=data.reserved_quantity,
            variant_id=variant_id,
        )
