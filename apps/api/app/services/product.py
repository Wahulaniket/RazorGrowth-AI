"""
Product service.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductSearchRequest, ProductUpdate


class ProductService:

    @staticmethod
    async def create(
        db: AsyncSession,
        tenant_id: UUID,
        data: ProductCreate,
    ):
        # Validate category exists and belongs to tenant
        category = await CategoryRepository.get_by_id(db, data.category_id)
        if not category or category.tenant_id != tenant_id:
            raise NotFoundError(resource="Category")

        # Validate SKU uniqueness
        existing_sku = await ProductRepository.get_by_sku(db, tenant_id, data.sku)
        if existing_sku:
            raise ConflictError(message="Product SKU already exists for this tenant.")

        # Validate slug uniqueness
        existing_slug = await ProductRepository.get_by_slug(db, tenant_id, data.slug)
        if existing_slug:
            raise ConflictError(message="Product slug already exists for this tenant.")

        return await ProductRepository.create(
            db,
            tenant_id=tenant_id,
            sku=data.sku,
            name=data.name,
            slug=data.slug,
            category_id=data.category_id,
            base_price=data.base_price,
            currency=data.currency,
            description=data.description,
            brand=data.brand,
            metadata=data.metadata,
        )

    @staticmethod
    async def get(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
    ):
        product = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, product_id,
        )
        if not product:
            raise NotFoundError(resource="Product")
        return product

    @staticmethod
    async def list(
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID | None = None,
        status: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        products, total = await ProductRepository.list_by_tenant(
            db, tenant_id,
            category_id=category_id,
            status=status,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            offset=offset,
        )
        return products, total

    @staticmethod
    async def search(
        db: AsyncSession,
        tenant_id: UUID,
        data: ProductSearchRequest,
    ):
        products, total = await ProductRepository.search(
            db, tenant_id,
            query_text=data.query,
            filters=data.filters,
            limit=data.limit,
            offset=data.offset,
        )
        return products, total

    @staticmethod
    async def update(
        db: AsyncSession,
        tenant_id: UUID,
        product_id: UUID,
        data: ProductUpdate,
    ):
        product = await ProductRepository.get_by_id_for_tenant(
            db, tenant_id, product_id,
        )
        if not product:
            raise NotFoundError(resource="Product")

        update_data = data.model_dump(exclude_unset=True)

        if "slug" in update_data and update_data["slug"] != product.slug:
            existing = await ProductRepository.get_by_slug(
                db, tenant_id, update_data["slug"],
            )
            if existing:
                raise ConflictError(message="Product slug already exists.")

        if "category_id" in update_data:
            cat = await CategoryRepository.get_by_id(db, update_data["category_id"])
            if not cat or cat.tenant_id != tenant_id:
                raise NotFoundError(resource="Category")

        return await ProductRepository.update(db, product, **update_data)
