"""
Product repository.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        product_id: UUID,
    ) -> Product | None:
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id_for_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
    ) -> Product | None:
        result = await db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_sku(
        db: AsyncSession,
        tenant_id: UUID,
        sku: str,
    ) -> Product | None:
        result = await db.execute(
            select(Product).where(
                Product.tenant_id == tenant_id,
                Product.sku == sku,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(
        db: AsyncSession,
        tenant_id: UUID,
        slug: str,
    ) -> Product | None:
        result = await db.execute(
            select(Product).where(
                Product.tenant_id == tenant_id,
                Product.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID | None = None,
        status: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Product], int]:
        """Return (products, total_count) for paginated listing."""
        query = select(Product).where(Product.tenant_id == tenant_id)
        count_query = select(func.count(Product.id)).where(Product.tenant_id == tenant_id)

        if category_id:
            query = query.where(Product.category_id == category_id)
            count_query = count_query.where(Product.category_id == category_id)
        if status:
            query = query.where(Product.status == status)
            count_query = count_query.where(Product.status == status)
        if min_price is not None:
            query = query.where(Product.base_price >= min_price)
            count_query = count_query.where(Product.base_price >= min_price)
        if max_price is not None:
            query = query.where(Product.base_price <= max_price)
            count_query = count_query.where(Product.base_price <= max_price)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)

        return list(result.scalars().all()), total

    @staticmethod
    async def search(
        db: AsyncSession,
        tenant_id: UUID,
        query_text: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Product], int]:
        """Text search on product name/description + filters."""
        query = select(Product).where(Product.tenant_id == tenant_id)
        count_query = select(func.count(Product.id)).where(Product.tenant_id == tenant_id)

        if query_text:
            search_filter = or_(
                Product.name.ilike(f"%{query_text}%"),
                Product.description.ilike(f"%{query_text}%"),
                Product.brand.ilike(f"%{query_text}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if filters:
            if "category" in filters:
                from app.models.category import Category
                cat_subq = select(Category.id).where(
                    Category.tenant_id == tenant_id,
                    Category.slug == filters["category"],
                ).scalar_subquery()
                query = query.where(Product.category_id == cat_subq)
                count_query = count_query.where(Product.category_id == cat_subq)
            if "max_price" in filters:
                query = query.where(Product.base_price <= filters["max_price"])
                count_query = count_query.where(Product.base_price <= filters["max_price"])
            if "min_price" in filters:
                query = query.where(Product.base_price >= filters["min_price"])
                count_query = count_query.where(Product.base_price >= filters["min_price"])
            if "status" in filters:
                query = query.where(Product.status == filters["status"])
                count_query = count_query.where(Product.status == filters["status"])

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Product.name).limit(limit).offset(offset)
        result = await db.execute(query)

        return list(result.scalars().all()), total

    @staticmethod
    async def create(
        db: AsyncSession,
        tenant_id: UUID,
        sku: str,
        name: str,
        slug: str,
        category_id: UUID,
        base_price: Decimal,
        currency: str = "INR",
        description: str | None = None,
        brand: str | None = None,
        metadata: dict | None = None,
    ) -> Product:
        product = Product(
            tenant_id=tenant_id,
            sku=sku,
            name=name,
            slug=slug,
            category_id=category_id,
            base_price=base_price,
            currency=currency,
            description=description,
            brand=brand,
            metadata_=metadata or {},
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def update(
        db: AsyncSession,
        product: Product,
        **kwargs,
    ) -> Product:
        for key, value in kwargs.items():
            if value is not None:
                if key == "metadata":
                    setattr(product, "metadata_", value)
                else:
                    setattr(product, key, value)
        await db.commit()
        await db.refresh(product)
        return product
