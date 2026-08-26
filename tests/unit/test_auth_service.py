"""
Unit tests for the auth service.
"""

import uuid
import pytest

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import verify_password
from app.schemas.auth import UserLogin, UserRegister
from app.services.auth import AuthService


@pytest.mark.asyncio
async def test_register_user_success(db):
    """Test successful user registration."""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    data = UserRegister(
        email=email,
        name="Test User",
        password="securepassword123",
    )
    
    user = await AuthService.register(db, data)
    
    assert user.id is not None
    assert user.email == email
    assert user.name == "Test User"
    assert verify_password("securepassword123", user.password_hash)


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db):
    """Test 409 conflict when email already exists."""
    email = f"duplicate-{uuid.uuid4().hex[:8]}@example.com"
    data = UserRegister(
        email=email,
        name="Original",
        password="password123",
    )
    
    await AuthService.register(db, data)
    
    with pytest.raises(ConflictError) as exc_info:
        await AuthService.register(db, data)
        
    assert exc_info.value.code == "CONFLICT"


@pytest.mark.asyncio
async def test_login_success(db):
    """Test successful login returns a JWT."""
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    data = UserRegister(
        email=email,
        name="Login Test",
        password="securepassword123",
    )
    await AuthService.register(db, data)
    
    login_data = UserLogin(
        email=email,
        password="securepassword123",
    )
    
    token = await AuthService.login(db, login_data)
    assert isinstance(token, str)
    assert len(token) > 20


@pytest.mark.asyncio
async def test_login_invalid_password(db):
    """Test 401 when password is incorrect."""
    email = f"wrongpass-{uuid.uuid4().hex[:8]}@example.com"
    data = UserRegister(
        email=email,
        name="Wrong Pass Test",
        password="correctpassword",
    )
    await AuthService.register(db, data)
    
    login_data = UserLogin(
        email=email,
        password="wrongpassword",
    )
    
    with pytest.raises(AuthenticationError) as exc_info:
        await AuthService.login(db, login_data)
        
    assert exc_info.value.code == "AUTHENTICATION_REQUIRED"
