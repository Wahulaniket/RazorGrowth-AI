"""fix rls policies nullif

Revision ID: 3d39a3b994bc
Revises: f08457ecb633
Create Date: 2026-08-27 22:54:05.782718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d39a3b994bc'
down_revision: Union[str, None] = 'f08457ecb633'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use NULLIF to handle missing context which returns empty string
    RLS_TABLES = [
        "tenant_memberships",
        "categories",
        "products",
        "product_variants",
        "api_keys"
    ]
    
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS select_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS insert_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS update_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS delete_policy ON {table};")
        
        op.execute(f"CREATE POLICY select_policy ON {table} FOR SELECT USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);")
        op.execute(f"CREATE POLICY insert_policy ON {table} FOR INSERT WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);")
        op.execute(f"CREATE POLICY update_policy ON {table} FOR UPDATE USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);")
        op.execute(f"CREATE POLICY delete_policy ON {table} FOR DELETE USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);")
        
    op.execute(f"DROP POLICY IF EXISTS select_policy ON audit_logs;")
    op.execute(f"DROP POLICY IF EXISTS insert_policy ON audit_logs;")
    op.execute("CREATE POLICY select_policy ON audit_logs FOR SELECT USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);")
    op.execute("CREATE POLICY insert_policy ON audit_logs FOR INSERT WITH CHECK (tenant_id IS NULL OR tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);")


def downgrade() -> None:
    # Downgrade reverts to just current_setting (which fails on empty string)
    RLS_TABLES = [
        "tenant_memberships",
        "categories",
        "products",
        "product_variants",
        "api_keys"
    ]
    
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS select_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS insert_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS update_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS delete_policy ON {table};")
        
        op.execute(f"CREATE POLICY select_policy ON {table} FOR SELECT USING (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        op.execute(f"CREATE POLICY insert_policy ON {table} FOR INSERT WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        op.execute(f"CREATE POLICY update_policy ON {table} FOR UPDATE USING (tenant_id = current_setting('app.current_tenant', true)::uuid) WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        op.execute(f"CREATE POLICY delete_policy ON {table} FOR DELETE USING (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        
    op.execute(f"DROP POLICY IF EXISTS select_policy ON audit_logs;")
    op.execute(f"DROP POLICY IF EXISTS insert_policy ON audit_logs;")
    op.execute("CREATE POLICY select_policy ON audit_logs FOR SELECT USING (tenant_id = current_setting('app.current_tenant', true)::uuid);")
    op.execute("CREATE POLICY insert_policy ON audit_logs FOR INSERT WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant', true)::uuid);")
