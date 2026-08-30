"""enforce_safe_rls_pattern

Revision ID: 7ed1b7b32459
Revises: 40a745594725
Create Date: 2026-08-31 01:01:55.050087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ed1b7b32459'
down_revision: Union[str, None] = '40a745594725'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tables = [
        "agent_decisions", "agent_tool_calls", "ai_messages", "ai_sessions",
        "analytics_events", "api_keys", "audit_logs", "cart_items", "carts",
        "categories", "checkout_confirmations", "checkout_quotes",
        "experiment_participants", "experiments", "inventory", "order_items",
        "orders", "payments", "payment_attempts", "policies", "product_relationships",
        "product_variants", "products", "recommendations", "tenant_memberships",
        "webhook_events"
    ]
    
    for table in tables:
        # Check if policy exists, if so drop and recreate to be safe, 
        # or just ALTER POLICY. ALTER POLICY requires the policy to exist.
        op.execute(f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_policies 
                WHERE tablename = '{table}' AND policyname = 'tenant_isolation_policy'
            ) THEN
                ALTER POLICY tenant_isolation_policy ON {table} 
                USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);
            END IF;
        END
        $$;
        """)


def downgrade() -> None:
    pass
