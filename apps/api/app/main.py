from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.error_handler import (
    razorgrowth_error_handler,
    unhandled_error_handler,
)
from app.api.middleware.request_id import RequestIDMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.products import router as products_router
from app.api.routes.tenants import router as tenant_router
from app.api.routes.users import router as users_router
from app.core.exceptions import RazorGrowthError
from app.db.session import get_db


app = FastAPI(
    title="RazorGrowth AI API",
    version="1.0.0",
    description="AI-native Agentic Commerce Platform",
)

# --- Middleware (order matters: outermost first) ---

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Error Handlers ---

app.add_exception_handler(RazorGrowthError, razorgrowth_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# --- Routers ---

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")


# --- Health Check ---

@app.get("/api/v1/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "service": "razorgrowth-api",
        "database": "ok",
    }