from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_tenant, require_permission
from app.core.permissions import PermissionEnum
from app.db.session import get_db
from app.models.tenant import Tenant
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse
from app.services.api_key import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["API Keys"])
api_key_service = ApiKeyService()


@router.post(
    "",
    response_model=ApiKeyCreateResponse,
    dependencies=[Depends(require_permission(PermissionEnum.API_KEYS_WRITE))],
)
async def create_api_key(
    data: ApiKeyCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new API key. The raw secret is returned ONLY once.
    """
    key = await api_key_service.create_api_key(db, tenant.id, data)
    await db.commit()
    return key


@router.get(
    "",
    response_model=List[ApiKeyResponse],
    dependencies=[Depends(require_permission(PermissionEnum.API_KEYS_READ))],
)
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List API keys for the current tenant.
    """
    return await api_key_service.list_api_keys(db, tenant.id, skip, limit)


@router.delete(
    "/{key_id}",
    response_model=ApiKeyResponse,
    dependencies=[Depends(require_permission(PermissionEnum.API_KEYS_WRITE))],
)
async def revoke_api_key(
    key_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke an API key.
    """
    key = await api_key_service.revoke_api_key(db, tenant.id, key_id)
    await db.commit()
    return key
