"""fix lookup_api_key_for_auth type mismatch

Revision ID: 9f4e9231e14b
Revises: 3d39a3b994bc
Create Date: 2026-08-28 23:28:27.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f4e9231e14b'
down_revision: Union[str, None] = '3d39a3b994bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Redeclare function casting key_hash to text
    op.execute("""
    CREATE OR REPLACE FUNCTION lookup_api_key_for_auth(p_prefix text)
    RETURNS TABLE (tenant_id uuid, key_hash text, id uuid, is_revoked boolean, expires_at timestamptz)
    SECURITY DEFINER
    SET search_path = public
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY SELECT a.tenant_id, a.key_hash::text, a.id, a.is_revoked, a.expires_at 
                     FROM api_keys a WHERE a.prefix = p_prefix;
    END;
    $$;
    """)


def downgrade() -> None:
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
