"""add rls policies and security definer

Revision ID: f08457ecb633
Revises: 05459fb7a9cd
Create Date: 2026-08-27 22:37:36.036796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f08457ecb633'
down_revision: Union[str, None] = '05459fb7a9cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RLS_TABLES = [
    'tenant_memberships',
    'categories',
    'products',
    'product_variants',
    'inventory',
    'product_relationships',
    'api_keys'
]

def upgrade() -> None:
    # 1. Create restricted Application Role
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'rg_app') THEN CREATE ROLE rg_app WITH LOGIN PASSWORD 'rg_app_dev'; END IF; END $$;")
    op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rg_app;")
    op.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rg_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO rg_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO rg_app;")
    
    # 2. RLS for standard tables
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        
        op.execute(f"CREATE POLICY select_policy ON {table} FOR SELECT USING (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        op.execute(f"CREATE POLICY insert_policy ON {table} FOR INSERT WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        op.execute(f"CREATE POLICY update_policy ON {table} FOR UPDATE USING (tenant_id = current_setting('app.current_tenant', true)::uuid) WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);")
        op.execute(f"CREATE POLICY delete_policy ON {table} FOR DELETE USING (tenant_id = current_setting('app.current_tenant', true)::uuid);")

    # 3. RLS for audit_logs (allows NULL tenant_id for pre-auth events)
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;")
    op.execute("CREATE POLICY select_policy ON audit_logs FOR SELECT USING (tenant_id = current_setting('app.current_tenant', true)::uuid);")
    op.execute("CREATE POLICY insert_policy ON audit_logs FOR INSERT WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.current_tenant', true)::uuid);")
    op.execute("CREATE POLICY update_policy ON audit_logs FOR UPDATE USING (false);") # audit logs are append-only
    op.execute("CREATE POLICY delete_policy ON audit_logs FOR DELETE USING (false);") # audit logs are append-only

    # 4. SECURITY DEFINER function for API Keys
    op.execute("""
    CREATE OR REPLACE FUNCTION lookup_api_key_for_auth(p_prefix text)
    RETURNS TABLE (tenant_id uuid, key_hash text, id uuid, is_revoked boolean, expires_at timestamptz)
    SECURITY DEFINER
    SET search_path = public
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY SELECT a.tenant_id, a.key_hash, a.id, a.is_revoked, a.expires_at 
                     FROM api_keys a WHERE a.prefix = p_prefix;
    END;
    $$;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS lookup_api_key_for_auth(text);")
    
    op.execute("DROP POLICY IF EXISTS select_policy ON audit_logs;")
    op.execute("DROP POLICY IF EXISTS insert_policy ON audit_logs;")
    op.execute("DROP POLICY IF EXISTS update_policy ON audit_logs;")
    op.execute("DROP POLICY IF EXISTS delete_policy ON audit_logs;")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;")
    
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS select_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS insert_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS update_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS delete_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM rg_app;")
    op.execute("REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM rg_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM rg_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM rg_app;")
    op.execute("DROP ROLE IF EXISTS rg_app;")
