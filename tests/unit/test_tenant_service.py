"""
Unit tests for the tenant service.
"""

import uuid
import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.tenant import TenantCreate
from app.services.tenant import TenantService


@pytest.mark.asyncio
async def test_create_tenant_success(db):
    """Test successful tenant creation."""
    slug = f"test-slug-{uuid.uuid4().hex[:8]}"
    data = TenantCreate(
        name="Test Name",
        slug=slug,
        default_currency="INR",
        timezone="Asia/Kolkata",
    )
    
    tenant = await TenantService.create(db, data)
    
    assert tenant.id is not None
    assert tenant.name == "Test Name"
    assert tenant.slug == slug


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(db):
    """Test 409 conflict when slug already exists."""
    slug = f"duplicate-{uuid.uuid4().hex[:8]}"
    data = TenantCreate(
        name="Original",
        slug=slug,
        default_currency="INR",
        timezone="Asia/Kolkata",
    )
    
    await TenantService.create(db, data)
    
    # Try to create again with same slug
    data2 = TenantCreate(
        name="Duplicate",
        slug=slug,
        default_currency="INR",
        timezone="Asia/Kolkata",
    )
    
    with pytest.raises(ConflictError) as exc_info:
        await TenantService.create(db, data2)
        
    assert exc_info.value.code == "CONFLICT"


@pytest.mark.asyncio
async def test_get_tenant_not_found(db):
    """Test 404 when tenant doesn't exist."""
    fake_id = str(uuid.uuid4())
    
    with pytest.raises(NotFoundError) as exc_info:
        await TenantService.get(db, fake_id)
        
    assert exc_info.value.code == "RESOURCE_NOT_FOUND"
