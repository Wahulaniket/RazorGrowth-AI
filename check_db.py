import asyncio
import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/api')))

from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        print("=== ROLES ===")
        res = await session.execute(text("SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication, rolbypassrls FROM pg_roles WHERE rolname = 'rg_app';"))
        for row in res:
            print(dict(row._mapping))
            
        print("\n=== POLICIES ===")
        res = await session.execute(text("SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename;"))
        for row in res:
            print(dict(row._mapping))
            
        print("\n=== ROW SECURITY ===")
        res = await session.execute(text("SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';"))
        for row in res:
            print(dict(row._mapping))
            
        print("\n=== SEC DEFINER ===")
        res = await session.execute(text("SELECT p.proname, p.prosecdef FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public' AND p.proname IN ('lookup_api_key_for_auth', 'get_current_tenant');"))
        for row in res:
            print(dict(row._mapping))
            
        print("\n=== GRANTS ===")
        res = await session.execute(text("SELECT table_schema, table_name, privilege_type FROM information_schema.role_table_grants WHERE grantee = 'rg_app';"))
        for row in res:
            print(dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(main())
