"""
AI Catalog API Routes.
Provides a clean, tool-compatible interface for AI agents to retrieve catalog data.
These endpoints expose only AI-readable representations and enforce strict limits.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_tenant
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.ai_catalog import (
    AIAvailabilityResponse,
    AICatalogSearchRequest,
    AICatalogSearchResponse,
    AIProductResponse,
    AIRelationshipResponse,
    AIVariantResponse,
)
from app.services.ai_catalog import AICatalogService


router = APIRouter(
    prefix="/catalog",
    tags=["AI Catalog"],
)


@router.post(
    "/search",
    response_model=AICatalogSearchResponse,
)
async def catalog_search(
    data: AICatalogSearchRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Search products using natural language query and deterministic filters.
    Tool binding: catalog.search
    """
    products, total = await AICatalogService.search(db, tenant.id, data)
    
    return AICatalogSearchResponse(
        items=products,
        total=total,
        limit=data.limit,
        offset=data.offset,
    )


@router.get(
    "/products/{product_id}",
    response_model=AIProductResponse,
)
async def catalog_get_product(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific product and its variants.
    Tool binding: catalog.get_product
    """
    return await AICatalogService.get_product(db, tenant.id, product_id)


@router.get(
    "/products/{product_id}/variants/{variant_id}",
    response_model=AIVariantResponse,
)
async def catalog_get_variant(
    product_id: UUID,
    variant_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific product variant.
    Tool binding: catalog.get_variant
    """
    return await AICatalogService.get_variant(db, tenant.id, product_id, variant_id)


@router.get(
    "/products/{product_id}/availability",
    response_model=AIAvailabilityResponse,
)
async def catalog_check_availability(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Check current inventory availability for a product.
    Tool binding: catalog.check_availability
    """
    return await AICatalogService.check_availability(db, tenant.id, product_id)


@router.get(
    "/products/{product_id}/relationships",
    response_model=list[AIRelationshipResponse],
)
async def catalog_get_relationships(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve product relationships (e.g., upsell, cross-sell, accessories).
    Tool binding: catalog.get_relationships
    """
    return await AICatalogService.get_relationships(db, tenant.id, product_id)
