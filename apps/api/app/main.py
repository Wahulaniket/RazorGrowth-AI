from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.error_handler import (
    razorgrowth_error_handler,
    unhandled_error_handler,
)
from app.api.middleware.request_id import RequestIDMiddleware
from contextlib import asynccontextmanager

from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.products import router as products_router
from app.api.routes.tenants import router as tenant_router
from app.api.routes.users import router as users_router
from app.api.routes.api_keys import router as api_keys_router
from app.api.routes.catalog import router as catalog_router
from app.core.exceptions import RazorGrowthError
from app.db.session import get_db
from app.core.config import get_settings
from fastapi import APIRouter

settings = get_settings()

from redis.asyncio import Redis
import app.core.rate_limit as rate_limit

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Redis
    redis_client = Redis.from_url(settings.redis_url)
    rate_limit.redis_client = redis_client
    
    yield
    
    # Teardown
    await redis_client.close()

app = FastAPI(
    title="RazorGrowth AI API",
    version="1.0.0",
    description="AI-native Agentic Commerce Platform",
    openapi_url=f"/api/v1/openapi.json",
    docs_url=f"/api/v1/docs",
    redoc_url=f"/api/v1/redoc",
    lifespan=lifespan,
)

# --- Middleware (order matters: outermost first) ---

app.add_middleware(RequestIDMiddleware)

# CORS configuration
if settings.backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Error Handlers ---

app.add_exception_handler(RazorGrowthError, razorgrowth_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# --- Routers ---

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tenant_router)
api_router.include_router(api_keys_router)
api_router.include_router(catalog_router)

app.include_router(api_router, prefix="/api/v1")
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