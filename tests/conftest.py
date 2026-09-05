import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

# Set environment variables required by Settings BEFORE imports
os.environ["JWT_SECRET_KEY"] = "test_secret_for_pytest"
os.environ["BACKEND_CORS_ORIGINS"] = '["http://localhost:3000"]'
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["LLM_API_KEY"] = ""
os.environ["LLM_MODEL"] = "fake-model"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.tenant import Tenant
from app.models.user import User


# Use a test database for integration tests
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://rg_app:rg_app_dev@localhost:5432/razorgrowth"
)

engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def dispose_engine():
    yield
    await engine.dispose()


# @pytest.fixture(scope="session")
# def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
#     """Create an instance of the default event loop for the whole session."""
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session and rollback after the test."""
    # Actually create tables if they don't exist (only for isolated test DB)
    # Since we are using the main DB in this config, we rely on alembic having run.
    # We will use nested transactions for rolling back.
    
    async with engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        
        async_session = AsyncSession(bind=conn, expire_on_commit=False)
        
        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                conn.sync_connection.begin_nested()
                
        yield async_session
        
        await async_session.close()
        await conn.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client with database override."""
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email=f"test-{uuid.uuid4().hex[:8]}@example.com",
        name="Test User",
        password_hash=hash_password("password123"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_tenant(db: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        slug=f"test-tenant-{uuid.uuid4().hex[:8]}",
        default_currency="INR",
        timezone="Asia/Kolkata",
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    # Establish RLS context for subsequent queries in unit tests
    db.info["tenant_id"] = str(tenant.id)
    await db.execute(text("SELECT set_config('app.current_tenant', :tenant_id, true)"), {"tenant_id": str(tenant.id)})
    
    return tenant


@pytest_asyncio.fixture(scope="function")
async def tenant(test_tenant: Tenant) -> Tenant:
    """Alias for test_tenant for use in tests."""
    return test_tenant



@pytest_asyncio.fixture(scope="function")
async def authorized_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """Test client with valid JWT token."""
    token = create_access_token(data={"sub": str(test_user.id), "email": test_user.email})
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
