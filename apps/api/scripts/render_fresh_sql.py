"""Render the existing migrations for a NEW, isolated PostgreSQL schema only.

Usage (no deployment credentials needed): python scripts/render_fresh_sql.py > init.sql
Never use this for an existing schema: use Alembic normally instead.
"""
import argparse
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import re
import sys
import uuid

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
# Offline generation never connects. These are throwaway settings, not runtime secrets.
os.environ.update(DATABASE_URL="postgresql+psycopg://unused:unused@localhost/unused",
                  SUPABASE_ISSUER="https://example.supabase.co/auth/v1",
                  SUPABASE_JWKS_URL="https://example.supabase.co/auth/v1/.well-known/jwks.json",
                  ENCRYPTION_KEY="X6bCSnPOvr1s9bq3sXZlzJIvYj9SB9GksyD7pG_BB-c=",
                  PHONE_HASH_KEY="OFFLINE-SQL-ONLY-NOT-A-DEPLOYMENT-SECRET-123456",
                  ENVIRONMENT="test")
from alembic import command
from alembic.config import Config
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from app.models import MembershipDelta
from app.database import Base


def migration_sql(revision):
    output = StringIO()
    config = Config(str(API_ROOT / "alembic.ini"), output_buffer=output)
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    with redirect_stdout(StringIO()):
        command.upgrade(config, revision, sql=True)
    return output.getvalue().replace("BEGIN;", "").replace("COMMIT;", "")


def render(schema="oms"):
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise ValueError("Use a simple lower-case PostgreSQL schema name")
    dialect = postgresql.dialect()
    ledger = str(CreateTable(MembershipDelta.__table__).compile(dialect=dialect)) + ";\n"
    ledger += "\n".join(str(CreateIndex(index).compile(dialect=dialect)) + ";"
                          for index in MembershipDelta.__table__.indexes)
    rls_tables = ["alembic_version", *Base.metadata.tables.keys()]
    rls = "\n".join(f'ALTER TABLE "{schema}"."{table}" ENABLE ROW LEVEL SECURITY;' for table in rls_tables)
    root = uuid.uuid4()
    nodes = [f"INSERT INTO org_nodes (id,parent_id,kind,code,name,active) VALUES ('{root}',NULL,'THANA','uttara-model','Uttara Model Thana',true);"]
    for number in range(1,13):
        nodes.append(f"INSERT INTO org_nodes (id,parent_id,kind,code,name,active) VALUES ('{uuid.uuid4()}','{root}','WARD','ward-{number:02d}','Ward {number:02d}',true);")
    return ("-- NEW EMPTY SCHEMA ONLY. CREATE SCHEMA deliberately fails if it exists.\n"
            "-- No credentials, accounts, role grants or person records are created.\nBEGIN;\n"
            f'CREATE SCHEMA "{schema}";\nSET LOCAL search_path TO "{schema}";\n'
            + migration_sql("0002_access") + "\n" + ledger + "\n"
            + "UPDATE alembic_version SET version_num='0003_membership_ledger' WHERE version_num='0002_access';\n"
            + migration_sql("0003_membership_ledger:0005_personal_workspace") + "\n"
            + "\n".join(nodes) + "\n" + rls + f'\nREVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC;\n'
            + f'REVOKE ALL ON ALL TABLES IN SCHEMA "{schema}" FROM PUBLIC;\n'
            + f'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA "{schema}" FROM PUBLIC;\nCOMMIT;\n'
            + f'SELECT version_num FROM "{schema}".alembic_version;\n'
            + f'SELECT kind,count(*) FROM "{schema}".org_nodes GROUP BY kind ORDER BY kind;\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema",default="oms")
    args = parser.parse_args()
    print(render(args.schema))
