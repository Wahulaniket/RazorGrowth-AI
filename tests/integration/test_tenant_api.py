"""
Integration tests for the Tenant API.
"""

import uuid
import pytest


@pytest.mark.asyncio
async def test_create_tenant_unauthorized(client):
    """Test POST /api/v1/tenants without auth returns 401."""
    response = await client.post(
        "/api/v1/tenants",
        json={
            "name": "Test Tenant",
            "slug": "test-unauth",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_create_tenant_authorized(authorized_client):
    """Test POST /api/v1/tenants with auth succeeds."""
    slug = f"test-auth-{uuid.uuid4().hex[:8]}"
    response = await authorized_client.post(
        "/api/v1/tenants",
        json={
            "name": "Test Tenant",
            "slug": slug,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == slug
    assert "id" in data


@pytest.mark.asyncio
async def test_get_tenant_authorized(authorized_client, test_tenant):
    """Test GET /api/v1/tenants/{id} with auth succeeds."""
    response = await authorized_client.get(f"/api/v1/tenants/{test_tenant.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == test_tenant.slug
    assert data["name"] == test_tenant.name


@pytest.mark.asyncio
async def test_get_tenant_unauthorized(client, test_tenant):
    """Test GET /api/v1/tenants/{id} without auth fails."""
    response = await client.get(f"/api/v1/tenants/{test_tenant.id}")
    assert response.status_code == 401
    
    
@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint works and is public."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "x-request-id" in response.headers
