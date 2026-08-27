"""
Unit tests for Category service.
"""

import pytest
from uuid import uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category import CategoryService
from app.models.category import Category

pytestmark = pytest.mark.asyncio


async def test_create_category_success(db, tenant):
    data = CategoryCreate(name="Electronics", slug="electronics")
    category = await CategoryService.create(db, tenant.id, data)
    
    assert category.name == "Electronics"
    assert category.slug == "electronics"
    assert category.tenant_id == tenant.id


async def test_create_category_duplicate_slug(db, tenant):
    data = CategoryCreate(name="Electronics", slug="electronics")
    await CategoryService.create(db, tenant.id, data)
    
    with pytest.raises(ConflictError):
        await CategoryService.create(db, tenant.id, data)


async def test_create_subcategory(db, tenant):
    parent_data = CategoryCreate(name="Electronics", slug="electronics")
    parent = await CategoryService.create(db, tenant.id, parent_data)
    
    child_data = CategoryCreate(name="Laptops", slug="laptops", parent_id=parent.id)
    child = await CategoryService.create(db, tenant.id, child_data)
    
    assert child.parent_id == parent.id


async def test_get_category_not_found(db, tenant):
    with pytest.raises(NotFoundError):
        await CategoryService.get(db, tenant.id, uuid4())


async def test_list_top_level_categories(db, tenant):
    # Top-level
    c1 = await CategoryService.create(db, tenant.id, CategoryCreate(name="C1", slug="c1"))
    c2 = await CategoryService.create(db, tenant.id, CategoryCreate(name="C2", slug="c2"))
    
    # Subcategory
    await CategoryService.create(db, tenant.id, CategoryCreate(name="C1_1", slug="c1-1", parent_id=c1.id))
    
    # List top level
    top = await CategoryService.list(db, tenant.id, parent_id=None)
    assert len(top) == 2
    assert {c.slug for c in top} == {"c1", "c2"}
