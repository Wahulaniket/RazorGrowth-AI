"""fix rls policies for remaining tables

Revision ID: 71487ee8454b
Revises: 21bfabb87cf6
Create Date: 2026-08-29 17:34:51.938851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71487ee8454b'
down_revision: Union[str, None] = '21bfabb87cf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    RLS_TABLES = [
        "inventory",
        "product_relationships",
        "carts",
        "cart_items"
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


def downgrade() -> None:
    RLS_TABLES = [
        "inventory",
        "product_relationships",
        "carts",
        "cart_items"
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
