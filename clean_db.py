import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://rg_app:rg_app_dev@localhost:5432/razorgrowth"
)

async def clean():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE roles, permissions, tenants, users, products, categories CASCADE;"))
    print("Cleaned!")

asyncio.run(clean())
