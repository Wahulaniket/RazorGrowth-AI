"""
Unit tests for Product service.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate, ProductSearchRequest
from app.services.category import CategoryService
from app.services.product import ProductService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def category(db, tenant):
    return await CategoryService.create(
        db, tenant.id, CategoryCreate(name="Test Cat", slug="test-cat")
    )


async def test_create_product_success(db, tenant, category):
    data = ProductCreate(
        sku="TEST-SKU",
        name="Test Product",
        slug="test-product",
        category_id=category.id,
        base_price=Decimal("999.00"),
    )
    product = await ProductService.create(db, tenant.id, data)
    assert product.sku == "TEST-SKU"
    assert product.base_price == Decimal("999.00")
    assert product.category_id == category.id


async def test_create_product_duplicate_sku(db, tenant, category):
    data = ProductCreate(
        sku="TEST-SKU",
        name="Test Product",
        slug="test-product",
        category_id=category.id,
        base_price=Decimal("999.00"),
    )
    await ProductService.create(db, tenant.id, data)
    
    data2 = ProductCreate(
        sku="TEST-SKU",
        name="Another Product",
        slug="another-product",
        category_id=category.id,
        base_price=Decimal("100.00"),
    )
    with pytest.raises(ConflictError, match="SKU already exists"):
        await ProductService.create(db, tenant.id, data2)


async def test_create_product_invalid_category(db, tenant):
    data = ProductCreate(
        sku="TEST-SKU",
        name="Test Product",
        slug="test-product",
        category_id=uuid4(),
        base_price=Decimal("999.00"),
    )
    with pytest.raises(NotFoundError, match="Category"):
        await ProductService.create(db, tenant.id, data)


async def test_get_product_not_found(db, tenant):
    with pytest.raises(NotFoundError):
        await ProductService.get(db, tenant.id, uuid4())


async def test_search_products_by_text(db, tenant, category):
    await ProductService.create(db, tenant.id, ProductCreate(
        sku="SKU-1", name="Gaming Laptop", slug="gaming-laptop",
        category_id=category.id, base_price=Decimal("1000")
    ))
    await ProductService.create(db, tenant.id, ProductCreate(
        sku="SKU-2", name="Office Mouse", slug="office-mouse",
        category_id=category.id, base_price=Decimal("50")
    ))
    
    req = ProductSearchRequest(query="gaming")
    products, total = await ProductService.search(db, tenant.id, req)
    
    assert total == 1
    assert products[0].sku == "SKU-1"


async def test_search_products_by_filters(db, tenant, category):
    await ProductService.create(db, tenant.id, ProductCreate(
        sku="SKU-1", name="Product 1", slug="p1",
        category_id=category.id, base_price=Decimal("1000")
    ))
    await ProductService.create(db, tenant.id, ProductCreate(
        sku="SKU-2", name="Product 2", slug="p2",
        category_id=category.id, base_price=Decimal("2000")
    ))
    
    req = ProductSearchRequest(filters={"max_price": 1500})
    products, total = await ProductService.search(db, tenant.id, req)
    
    assert total == 1
    assert products[0].sku == "SKU-1"
