import secrets
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import hash_password
from app.models.api_key import ApiKey
from app.repositories.api_key import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse


class ApiKeyService:

    async def create_api_key(
        self, db: AsyncSession, tenant_id: UUID, data: ApiKeyCreate
    ) -> ApiKeyCreateResponse:
        """
        Creates a new API key. Returns the raw secret key ONCE.
        """
        # Generate 32 bytes of secure random hex (64 chars)
        raw_secret = secrets.token_hex(32)
        full_key = f"rg_live_{raw_secret}"
        
        # We store the first 16 characters as the prefix for lookup
        # e.g. prefix = "rg_live_a1b2c3d4..."
        prefix = full_key[:16]
        
        # Securely hash the full key
        key_hash = hash_password(full_key)
        
        api_key = ApiKey(
            tenant_id=tenant_id,
            name=data.name,
            prefix=prefix,
            key_hash=key_hash,
            is_revoked=False,
        )
        
        api_key = await ApiKeyRepository.create(db, api_key)
        
        # Construct response containing the raw secret
        response = ApiKeyCreateResponse(
            id=api_key.id,
            tenant_id=api_key.tenant_id,
            name=api_key.name,
            prefix=api_key.prefix,
            secret_key=full_key,
            is_revoked=api_key.is_revoked,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
        )
        return response

    async def list_api_keys(
        self, db: AsyncSession, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[ApiKey]:
        return await ApiKeyRepository.list_for_tenant(db, tenant_id, skip, limit)

    async def revoke_api_key(
        self, db: AsyncSession, tenant_id: UUID, key_id: UUID
    ) -> ApiKey:
        api_key = await ApiKeyRepository.get_by_id_for_tenant(db, tenant_id, key_id)
        if not api_key:
            raise NotFoundError(message="API Key not found.")
            
        api_key.is_revoked = True
        return await ApiKeyRepository.update(db, api_key)
