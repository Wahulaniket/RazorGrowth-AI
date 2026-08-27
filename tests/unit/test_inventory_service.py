"""
Unit tests for Inventory service.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.core.exceptions import NotFoundError
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate
from app.schemas.inventory import InventoryUpdate
from app.services.category import CategoryService
from app.services.product import ProductService
from app.services.inventory import InventoryService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def product(db, tenant):
    cat = await CategoryService.create(db, tenant.id, CategoryCreate(name="Cat", slug="cat"))
    return await ProductService.create(db, tenant.id, ProductCreate(
        sku="SKU-INV", name="Product", slug="prod-inv", category_id=cat.id, base_price=Decimal("100")
    ))


async def test_get_inventory_default_zero(db, tenant, product):
    inv = await InventoryService.get(db, tenant.id, product.id)
    assert isinstance(inv, dict)
    assert inv["available_quantity"] == 0
    assert inv["reserved_quantity"] == 0
    assert inv["in_stock"] is False


async def test_update_inventory(db, tenant, product):
    data = InventoryUpdate(available_quantity=10, reserved_quantity=2)
    inv = await InventoryService.update(db, tenant.id, product.id, data)
    
    assert inv.available_quantity == 10
    assert inv.reserved_quantity == 2
    
    # Retrieve it back
    fetched = await InventoryService.get(db, tenant.id, product.id)
    assert getattr(fetched, "available_quantity", 0) == 10


async def test_inventory_invalid_product(db, tenant):
    data = InventoryUpdate(available_quantity=10, reserved_quantity=0)
    with pytest.raises(NotFoundError):
        await InventoryService.update(db, tenant.id, uuid4(), data)
