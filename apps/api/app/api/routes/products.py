"""
Product routes.

Includes product CRUD, search, inventory, and relationships.
All routes require authentication + tenant scoping.
"""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_tenant
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.inventory import InventoryResponse, InventoryUpdate
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductSearchRequest,
    ProductUpdate,
)
from app.schemas.product_relationship import RelationshipCreate, RelationshipResponse
from app.schemas.product_variant import VariantCreate, VariantResponse, VariantUpdate
from app.services.inventory import InventoryService
from app.services.product import ProductService
from app.services.product_relationship import ProductRelationshipService


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def _product_to_response(product) -> ProductResponse:
    """Convert a Product model to ProductResponse, adding category_name."""
    return ProductResponse(
        id=product.id,
        tenant_id=product.tenant_id,
        category_id=product.category_id,
        category_name=product.category.name if product.category else None,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        description=product.description,
        status=product.status,
        brand=product.brand,
        base_price=product.base_price,
        currency=product.currency,
        metadata=product.metadata_,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


# --- Product CRUD ---


@router.post(
    "",
    response_model=ProductResponse,
    status_code=201,
)
async def create_product(
    data: ProductCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new product."""
    product = await ProductService.create(db, tenant.id, data)
    return _product_to_response(product)


@router.get(
    "",
    response_model=ProductListResponse,
)
async def list_products(
    category_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    min_price: Decimal | None = Query(default=None),
    max_price: Decimal | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List products with optional filters and pagination."""
    products, total = await ProductService.list(
        db, tenant.id,
        category_id=category_id,
        status=status,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
    )
    return ProductListResponse(
        items=[_product_to_response(p) for p in products],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get a single product by ID."""
    product = await ProductService.get(db, tenant.id, product_id)
    return _product_to_response(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    product = await ProductService.update(db, tenant.id, product_id, data)
    return _product_to_response(product)


# --- Search ---


@router.post(
    "/search",
    response_model=ProductListResponse,
)
async def search_products(
    data: ProductSearchRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Search products by text query and/or filters.
    This is the primary AI catalog search endpoint.
    """
    products, total = await ProductService.search(db, tenant.id, data)
    return ProductListResponse(
        items=[_product_to_response(p) for p in products],
        total=total,
        limit=data.limit,
        offset=data.offset,
    )


# --- Inventory ---


@router.get(
    "/{product_id}/inventory",
    response_model=InventoryResponse,
)
async def get_inventory(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get inventory for a product."""
    inv = await InventoryService.get(db, tenant.id, product_id)
    if isinstance(inv, dict):
        return InventoryResponse(**inv)
    return InventoryResponse(
        product_id=inv.product_id,
        variant_id=inv.variant_id,
        available_quantity=inv.available_quantity,
        reserved_quantity=inv.reserved_quantity,
        in_stock=(inv.available_quantity - inv.reserved_quantity) > 0,
    )


@router.put(
    "/{product_id}/inventory",
    response_model=InventoryResponse,
)
async def update_inventory(
    product_id: UUID,
    data: InventoryUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update inventory for a product."""
    inv = await InventoryService.update(db, tenant.id, product_id, data)
    return InventoryResponse(
        product_id=inv.product_id,
        variant_id=inv.variant_id,
        available_quantity=inv.available_quantity,
        reserved_quantity=inv.reserved_quantity,
        in_stock=(inv.available_quantity - inv.reserved_quantity) > 0,
    )


# --- Relationships ---


@router.get(
    "/{product_id}/relationships",
    response_model=list[RelationshipResponse],
)
async def get_relationships(
    product_id: UUID,
    type: str | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get relationships for a product. Optionally filter by type."""
    rels = await ProductRelationshipService.list(
        db, tenant.id, product_id, type,
    )
    return [
        RelationshipResponse(
            id=r.id,
            source_product_id=r.source_product_id,
            target_product_id=r.target_product_id,
            target_product_name=r.target_product.name if r.target_product else None,
            relationship_type=r.relationship_type,
            score=r.score,
            metadata=r.metadata_,
            created_at=r.created_at,
        )
        for r in rels
    ]


@router.post(
    "/{product_id}/relationships",
    response_model=RelationshipResponse,
    status_code=201,
)
async def create_relationship(
    product_id: UUID,
    data: RelationshipCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a product relationship."""
    rel = await ProductRelationshipService.create(
        db, tenant.id, product_id, data,
    )
    return RelationshipResponse(
        id=rel.id,
        source_product_id=rel.source_product_id,
        target_product_id=rel.target_product_id,
        target_product_name=rel.target_product.name if rel.target_product else None,
        relationship_type=rel.relationship_type,
        score=rel.score,
        metadata=rel.metadata_,
        created_at=rel.created_at,
    )


# --- Variants ---


@router.post(
    "/{product_id}/variants",
    response_model=VariantResponse,
    status_code=201,
)
async def create_variant(
    product_id: UUID,
    data: VariantCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a product variant."""
    from app.core.exceptions import NotFoundError
    from app.models.product_variant import ProductVariant
    from app.repositories.product import ProductRepository

    product = await ProductRepository.get_by_id_for_tenant(db, tenant.id, product_id)
    if not product:
        raise NotFoundError(resource="Product")

    variant = ProductVariant(
        product_id=product_id,
        sku=data.sku,
        name=data.name,
        price=data.price,
        currency=data.currency,
        attributes=data.attributes,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return variant


@router.get(
    "/{product_id}/variants",
    response_model=list[VariantResponse],
)
async def list_variants(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List variants for a product."""
    from app.core.exceptions import NotFoundError
    from app.repositories.product import ProductRepository

    product = await ProductRepository.get_by_id_for_tenant(db, tenant.id, product_id)
    if not product:
        raise NotFoundError(resource="Product")

    return product.variants
