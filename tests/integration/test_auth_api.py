"""
Integration tests for the Auth API.
"""

import uuid
import pytest


@pytest.mark.asyncio
async def test_register_api(client):
    """Test POST /api/v1/auth/register creates user."""
    email = f"api-{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "API User",
            "password": "strongpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["name"] == "API User"
    assert "id" in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_login_api(client):
    """Test POST /api/v1/auth/login returns token."""
    email = f"login-api-{uuid.uuid4().hex[:8]}@example.com"
    password = "strongpassword123"
    
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "API Login User",
            "password": password,
        },
    )
    
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_me(authorized_client, test_user):
    """Test GET /api/v1/auth/me returns current user."""
    response = await authorized_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name
    assert "password_hash" not in data
