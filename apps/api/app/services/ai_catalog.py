"""
AI Catalog Service.
Provides an AI-specific abstraction over the catalog, enforcing deterministic
filtering, lexical search, and safety boundaries.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_relationship import ProductRelationship
from app.models.product_variant import ProductVariant
from app.schemas.ai_catalog import (
    AIAvailabilityResponse,
    AICatalogSearchRequest,
    AIProductResponse,
    AIRelationshipResponse,
    AIVariantResponse,
)


class AICatalogService:
    @staticmethod
    def _to_ai_product(product: Product) -> AIProductResponse:
        """Map Product model to AIProductResponse."""
        variants = [
            AIVariantResponse(
                id=v.id,
                sku=v.sku,
                name=v.name,
                price=v.price,
                currency=v.currency,
                attributes=v.attributes,
            )
            for v in product.variants
        ]
        
        return AIProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category=product.category.slug if product.category else None,
            brand=product.brand,
            price=product.base_price,
            currency=product.currency,
            attributes=product.metadata_,
            variants=variants,
        )

    @staticmethod
    async def search(
        db: AsyncSession, tenant_id: UUID, req: AICatalogSearchRequest
    ) -> tuple[list[AIProductResponse], int]:
        """
        Deterministic retrieval abstraction.
        Currently implements ILIKE lexical search and exact filtering.
        """
        # Base query (only ACTIVE products)
        stmt = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.variants)
        ).where(Product.status == "ACTIVE")
        
        # We don't filter on tenant_id explicitly here because RLS enforces it.
        # However, we can add it defensively if we want, but the transaction context handles it.

        # Text query (ILIKE on name or description)
        if req.query:
            search_term = f"%{req.query}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                )
            )

        # Category filter
        if req.category:
            stmt = stmt.join(Category).where(Category.slug == req.category)
            
        # Price filters
        if req.min_price is not None:
            stmt = stmt.where(Product.base_price >= req.min_price)
        if req.max_price is not None:
            stmt = stmt.where(Product.base_price <= req.max_price)
            
        # Inventory filter
        if req.in_stock_only:
            # Requires available_quantity > reserved_quantity
            stmt = stmt.join(Inventory, Inventory.product_id == Product.id).where(
                (Inventory.available_quantity - Inventory.reserved_quantity) > 0
            )
            
        # Attribute exact matching via JSONB
        for key, value in req.attributes.items():
            stmt = stmt.where(Product.metadata_[key].astext == str(value))
            
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar() or 0
        
        # Paginate
        stmt = stmt.limit(req.limit).offset(req.offset)
        
        res = await db.execute(stmt)
        products = res.scalars().all()
        
        return [AICatalogService._to_ai_product(p) for p in products], total

    @staticmethod
    async def get_product(
        db: AsyncSession, tenant_id: UUID, product_id: UUID
    ) -> AIProductResponse:
        """Retrieve a single active product."""
        stmt = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.variants)
        ).where(Product.id == product_id, Product.status == "ACTIVE")
        
        res = await db.execute(stmt)
        product = res.scalar_one_or_none()
        
        if not product:
            raise NotFoundError(resource="Product")
            
        return AICatalogService._to_ai_product(product)

    @staticmethod
    async def get_variant(
        db: AsyncSession, tenant_id: UUID, product_id: UUID, variant_id: UUID
    ) -> AIVariantResponse:
        """Retrieve a specific product variant."""
        stmt = select(ProductVariant).join(Product).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
            Product.status == "ACTIVE"
        )
        
        res = await db.execute(stmt)
        variant = res.scalar_one_or_none()
        
        if not variant:
            raise NotFoundError(resource="ProductVariant")
            
        return AIVariantResponse(
            id=variant.id,
            sku=variant.sku,
            name=variant.name,
            price=variant.price,
            currency=variant.currency,
            attributes=variant.attributes,
        )

    @staticmethod
    async def check_availability(
        db: AsyncSession, tenant_id: UUID, product_id: UUID
    ) -> AIAvailabilityResponse:
        """Check inventory availability for a product."""
        # Ensure product exists and is active
        product_stmt = select(Product.id).where(
            Product.id == product_id, Product.status == "ACTIVE"
        )
        if not (await db.execute(product_stmt)).scalar_one_or_none():
            raise NotFoundError(resource="Product")
            
        # Check overall inventory (assuming default variant logic for now)
        inv_stmt = select(Inventory).where(Inventory.product_id == product_id)
        res = await db.execute(inv_stmt)
        inv = res.scalars().first()
        
        if not inv:
            return AIAvailabilityResponse(
                product_id=product_id,
                available_quantity=0,
                reserved_quantity=0,
                in_stock=False,
            )
            
        return AIAvailabilityResponse(
            product_id=inv.product_id,
            variant_id=inv.variant_id,
            available_quantity=inv.available_quantity,
            reserved_quantity=inv.reserved_quantity,
            in_stock=(inv.available_quantity - inv.reserved_quantity) > 0,
        )

    @staticmethod
    async def get_relationships(
        db: AsyncSession, tenant_id: UUID, product_id: UUID
    ) -> list[AIRelationshipResponse]:
        """Retrieve relationships for a product (e.g., UPSELL, ACCESSORY)."""
        # Ensure product exists and is active
        product_stmt = select(Product.id).where(
            Product.id == product_id, Product.status == "ACTIVE"
        )
        if not (await db.execute(product_stmt)).scalar_one_or_none():
            raise NotFoundError(resource="Product")
            
        stmt = select(ProductRelationship).where(
            ProductRelationship.source_product_id == product_id
        )
        
        res = await db.execute(stmt)
        rels = res.scalars().all()
        
        return [
            AIRelationshipResponse(
                target_product_id=r.target_product_id,
                relationship_type=r.relationship_type,
                score=r.score,
            )
            for r in rels
        ]
