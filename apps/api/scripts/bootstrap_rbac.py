"""
RBAC Bootstrap Script

Idempotently creates standard roles, permissions, and initial tenant memberships.
Run this script to initialize or update the RBAC configuration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure the app directory is in the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.permissions import PermissionEnum
from app.db.session import AsyncSessionLocal
from app.models.role import Permission, Role, RolePermission
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the standard roles and their assigned permissions
DEFAULT_ROLES = {
    "Admin": {
        "description": "Full access to all tenant resources",
        "permissions": [
            PermissionEnum.CATALOG_READ,
            PermissionEnum.CATALOG_WRITE,
            PermissionEnum.API_KEYS_READ,
            PermissionEnum.API_KEYS_WRITE,
            PermissionEnum.TENANT_READ,
            PermissionEnum.TENANT_WRITE,
            PermissionEnum.AGENT_USE,
            PermissionEnum.POLICIES_READ,
            PermissionEnum.POLICIES_WRITE,
        ]
    },
    "Manager": {
        "description": "Can manage catalog and use agent, but cannot manage tenant settings or API keys",
        "permissions": [
            PermissionEnum.CATALOG_READ,
            PermissionEnum.CATALOG_WRITE,
            PermissionEnum.TENANT_READ,
            PermissionEnum.AGENT_USE,
        ]
    },
    "Viewer": {
        "description": "Read-only access to the catalog and tenant information",
        "permissions": [
            PermissionEnum.CATALOG_READ,
            PermissionEnum.TENANT_READ,
        ]
    }
}


async def bootstrap_rbac(db: AsyncSession) -> None:
    """Idempotently bootstrap roles and permissions."""
    logger.info("Starting RBAC bootstrap...")

    # 1. Ensure all defined permissions exist
    logger.info("Ensuring permissions exist...")
    all_permissions = list(PermissionEnum)
    for perm_enum in all_permissions:
        stmt = select(Permission).where(Permission.name == perm_enum.value)
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        
        if not perm:
            logger.info(f"Creating permission: {perm_enum.value}")
            perm = Permission(name=perm_enum.value, description=f"Allows {perm_enum.value}")
            db.add(perm)
    
    await db.flush()  # Flush so permissions have IDs

    # Reload all permissions into a mapping
    result = await db.execute(select(Permission))
    db_permissions = {p.name: p for p in result.scalars().all()}

    # 2. Ensure all defined roles exist and have the correct permissions
    logger.info("Ensuring roles exist...")
    for role_name, role_def in DEFAULT_ROLES.items():
        stmt = select(Role).where(Role.name == role_name)
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()
        
        if not role:
            logger.info(f"Creating role: {role_name}")
            role = Role(name=role_name, description=role_def["description"])
            db.add(role)
            await db.flush()
        
        # 3. Map permissions to the role
        # First, fetch existing mappings to avoid integrity errors
        stmt = select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
        result = await db.execute(stmt)
        existing_perm_ids = {pid for pid in result.scalars().all()}
        
        desired_perm_names = [p.value for p in role_def["permissions"]]
        
        for p_name in desired_perm_names:
            perm_obj = db_permissions.get(p_name)
            if perm_obj and perm_obj.id not in existing_perm_ids:
                logger.info(f"Assigning {p_name} to {role_name}")
                rp = RolePermission(role_id=role.id, permission_id=perm_obj.id)
                db.add(rp)
                
    await db.commit()
    logger.info("RBAC bootstrap completed successfully.")


async def bootstrap_initial_user(db: AsyncSession, email: str, tenant_slug: str, role_name: str) -> None:
    """Link the initial user to the initial tenant if they exist."""
    logger.info(f"Checking for initial user '{email}' and tenant '{tenant_slug}'...")
    
    # Find user
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User '{email}' not found. Skipping initial membership creation.")
        return
        
    # Find tenant
    stmt = select(Tenant).where(Tenant.slug == tenant_slug)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    
    if not tenant:
        logger.warning(f"Tenant '{tenant_slug}' not found. Skipping initial membership creation.")
        return
        
    # Find role
    stmt = select(Role).where(Role.name == role_name)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    
    if not role:
        logger.error(f"Role '{role_name}' not found. Ensure RBAC bootstrap ran first.")
        return
        
    # Check if membership already exists
    stmt = select(TenantMembership).where(
        TenantMembership.user_id == user.id,
        TenantMembership.tenant_id == tenant.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    
    if not membership:
        logger.info(f"Creating TenantMembership for {email} in {tenant_slug} as {role_name}")
        membership = TenantMembership(
            user_id=user.id,
            tenant_id=tenant.id,
            role_id=role.id
        )
        db.add(membership)
        
        try:
            await db.commit()
            logger.info("Initial user linked successfully.")
        except IntegrityError:
            await db.rollback()
            logger.info("Membership already exists (caught IntegrityError).")
    else:
        logger.info(f"Membership already exists for {email} in {tenant_slug}. No action needed.")
        
        # Optionally, ensure the role is correct
        if membership.role_id != role.id:
            logger.info(f"Updating role for {email} to {role_name}.")
            membership.role_id = role.id
            await db.commit()


async def main():
    async with AsyncSessionLocal() as db:
        await bootstrap_rbac(db)
        await bootstrap_initial_user(
            db, 
            email="test@example.com", 
            tenant_slug="techworld", 
            role_name="Admin"
        )


if __name__ == "__main__":
    asyncio.run(main())
