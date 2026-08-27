from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session

from app.core.config import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(Session, "after_begin")
def set_tenant_context(session: Session, transaction, connection):
    """
    Automatically set the transaction-local tenant context for RLS in PostgreSQL
    whenever a new transaction begins, if tenant_id is present in session.info.
    """
    tenant_id = session.info.get("tenant_id")
    if tenant_id:
        connection.execute(
            text("SELECT set_config('app.current_tenant', :tenant_id, true)"),
            {"tenant_id": tenant_id},
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session