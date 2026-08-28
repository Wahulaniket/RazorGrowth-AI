"""
Integration tests for the RBAC Bootstrap script.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionEnum
from app.models.role import Permission, Role, RolePermission
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership
from app.models.user import User

from scripts.bootstrap_rbac import bootstrap_rbac, bootstrap_initial_user, DEFAULT_ROLES

pytestmark = pytest.mark.asyncio


async def test_bootstrap_idempotency_and_creation(db: AsyncSession):
    """
    Test that running bootstrap_rbac twice does not fail,
    and accurately creates the specified roles and permissions.
    """
    # 1. Run bootstrap the first time
    await bootstrap_rbac(db)
    
    # 2. Run it again to prove idempotency
    await bootstrap_rbac(db)

    # 3. Assert Permissions are created
    stmt = select(Permission)
    result = await db.execute(stmt)
    db_permissions = result.scalars().all()
    
    expected_perm_names = {p.value for p in PermissionEnum}
    actual_perm_names = {p.name for p in db_permissions}
    
    assert expected_perm_names.issubset(actual_perm_names), "All Enum permissions must be seeded."
    
    # 4. Assert Roles are created
    stmt = select(Role)
    result = await db.execute(stmt)
    db_roles = result.scalars().all()
    
    expected_role_names = set(DEFAULT_ROLES.keys())
    actual_role_names = {r.name for r in db_roles}
    
    assert expected_role_names.issubset(actual_role_names), "All default roles must be seeded."
    
    # 5. Assert Admin has all its permissions
    stmt = select(Role).where(Role.name == "Admin")
    admin_role = (await db.execute(stmt)).scalar_one()
    
    stmt = select(Permission.name).join(RolePermission).where(RolePermission.role_id == admin_role.id)
    admin_perms = {name for name in (await db.execute(stmt)).scalars().all()}
    
    expected_admin_perms = {p.value for p in DEFAULT_ROLES["Admin"]["permissions"]}
    assert expected_admin_perms == admin_perms, "Admin role must have exactly its configured permissions."


async def test_bootstrap_initial_user_membership(db: AsyncSession, test_user: User, test_tenant: Tenant):
    """
    Test that bootstrap_initial_user correctly links the user to the tenant 
    with the specified role, and doesn't fail on re-run.
    """
    # Pre-requisite: run RBAC bootstrap so roles exist
    await bootstrap_rbac(db)
    
    # Run user bootstrap
    await bootstrap_initial_user(db, test_user.email, test_tenant.slug, "Admin")
    
    # Verify membership exists
    stmt = select(TenantMembership).where(
        TenantMembership.user_id == test_user.id,
        TenantMembership.tenant_id == test_tenant.id
    )
    membership = (await db.execute(stmt)).scalar_one_or_none()
    
    assert membership is not None, "Membership must be created."
    
    # Verify the role is Admin
    stmt = select(Role).where(Role.id == membership.role_id)
    role = (await db.execute(stmt)).scalar_one()
    assert role.name == "Admin", "User must be granted the Admin role."
    
    # Run user bootstrap again to prove idempotency
    await bootstrap_initial_user(db, test_user.email, test_tenant.slug, "Admin")
    
    # Verify no duplicate memberships were created
    stmt = select(TenantMembership).where(
        TenantMembership.user_id == test_user.id,
        TenantMembership.tenant_id == test_tenant.id
    )
    memberships = (await db.execute(stmt)).scalars().all()
    
    assert len(memberships) == 1, "Only one membership should exist per user/tenant."
