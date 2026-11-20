"""Exercise actual migrations and legacy event reconstruction on isolated synthetic DBs."""
import os
from pathlib import Path
import subprocess
import sys
import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
import pytest


def migrate(url, revision):
    environment = dict(os.environ, DATABASE_URL=url, ENVIRONMENT="test")
    return subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision],
                          cwd=Path(__file__).resolve().parents[1], env=environment,
                          capture_output=True, text=True)


@pytest.fixture
def migration_db(tmp_path):
    base_url = os.environ.get("TEST_DATABASE_URL")
    if base_url:
        from sqlalchemy.engine import make_url
        schema = "oms_migration_" + uuid.uuid4().hex
        admin = sa.create_engine(base_url)
        with admin.begin() as connection:
            connection.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
        url = make_url(base_url).update_query_dict({"options":f"-csearch_path={schema}"}).render_as_string(hide_password=False)
    else:
        url = "sqlite+pysqlite:///" + str(tmp_path / "migration.sqlite3")
    engine = sa.create_engine(url)
    try:
        yield url, engine
    finally:
        engine.dispose()
        if base_url:
            with admin.begin() as connection:
                connection.execute(sa.text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin.dispose()


def legacy_fixture(engine, complete=True):
    from app.database import Base
    from app import models
    metadata = Base.metadata
    ids = {k:uuid.uuid4() for k in ("root","ward","unit1","unit2","user","member")}
    now = datetime(2020,1,1,tzinfo=timezone.utc)
    with engine.begin() as c:
        org = metadata.tables["org_nodes"]
        c.execute(org.insert(), [dict(id=ids["root"],parent_id=None,kind="THANA",code="root",name="Test root",active=True)])
        c.execute(org.insert(), [dict(id=ids["ward"],parent_id=ids["root"],kind="WARD",code="ward",name="Test ward",active=True)])
        for unit in ("unit1","unit2"):
            c.execute(org.insert().values(id=ids[unit],parent_id=ids["ward"],kind="UNIT",code=unit,name="Test unit",active=True))
        c.execute(metadata.tables["app_users"].insert().values(id=ids["user"],auth_sub=str(ids["user"]),email="synthetic@example.invalid",active=True,created_at=now))
        c.execute(metadata.tables["members"].insert().values(id=ids["member"],member_number="LEGACY-01",full_name="Synthetic Legacy",category="RUKON",status="INACTIVE",org_node_id=ids["unit2"],consent_at=now,consent_version="test",version=4,created_at=now,updated_at=now))
        history = [("CREATED",None,"ACTIVE"),("CATEGORY","SUPPORTER","RUKON"),("TRANSFER",str(ids["unit1"]),str(ids["unit2"])),("DEACTIVATE","ACTIVE","INACTIVE")]
        for i,(action,before,after) in enumerate(history):
            if not complete and action == "CREATED": continue
            c.execute(metadata.tables["member_events"].insert().values(id=uuid.uuid4(),member_id=ids["member"],action=action,before=before,after=after,actor_id=ids["user"],created_at=now.replace(day=i+1)))
    return ids


def test_backfill_and_schema_match(migration_db):
    url, engine = migration_db
    result = migrate(url,"0002_access")
    assert result.returncode == 0, result.stderr
    ids = legacy_fixture(engine)
    result = migrate(url,"head")
    assert result.returncode == 0, result.stderr
    with engine.connect() as c:
        rows = c.execute(sa.text("SELECT category, sum(delta) FROM membership_deltas GROUP BY category")).all()
        assert all(count == 0 for _,count in rows)
        assert c.execute(sa.text("SELECT count(*) FROM membership_deltas")).scalar_one() == 6
        assert c.execute(sa.text("SELECT count(*) FROM members")).scalar_one() == 1
        assert c.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() == "0005_personal_workspace"
    result = subprocess.run([sys.executable,"-m","alembic","check"], cwd=Path(__file__).resolve().parents[1],env=dict(os.environ,DATABASE_URL=url,ENVIRONMENT="test"),capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    if engine.dialect.name == "postgresql":
        with pytest.raises(sa.exc.DBAPIError, match="append-only"):
            with engine.begin() as c:
                c.execute(sa.text("DELETE FROM membership_deltas"))


def test_backfill_rejects_incomplete_history(migration_db):
    url, engine = migration_db
    assert migrate(url,"0002_access").returncode == 0
    legacy_fixture(engine, complete=False)
    result = migrate(url,"head")
    assert result.returncode != 0
    assert "Missing legacy creation event" in result.stderr


def test_fresh_sql_renderer(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts" / "render_fresh_sql.py"
    schema = "oms_fresh_" + uuid.uuid4().hex
    result = subprocess.run([sys.executable,str(script),"--schema",schema],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    sql = result.stdout
    assert f'CREATE SCHEMA "{schema}";' in sql
    assert "IF NOT EXISTS" not in sql
    assert "0004_invariants" in sql
    assert sql.count("'WARD','ward-") == 12
    assert "CREATE TRIGGER oms_history_immutable" in sql
    assert "INSERT INTO members" not in sql
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "FROM PUBLIC" in sql
    base_url = os.environ.get("TEST_DATABASE_URL")
    if base_url:
        engine = sa.create_engine(base_url)
        try:
            with engine.connect() as c:
                c.exec_driver_sql(sql)
                assert c.execute(sa.text(f'SELECT count(*) FROM "{schema}".org_nodes')).scalar_one() == 13
                assert c.execute(sa.text(f'SELECT count(*) FROM "{schema}".members')).scalar_one() == 0
                assert c.execute(sa.text(f'SELECT version_num FROM "{schema}".alembic_version')).scalar_one() == "0005_personal_workspace"
                c.commit()
        finally:
            with engine.begin() as c:
                c.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
            engine.dispose()


def test_runtime_permissions_enforce_database_boundary():
    """Exercise the deployment grants under an actual restricted PostgreSQL role."""
    base_url = os.environ.get("TEST_DATABASE_URL")
    if not base_url:
        pytest.skip("Runtime grants require PostgreSQL")
    import re
    root = Path(__file__).resolve().parents[3]
    schema = "oms_runtime_test_" + uuid.uuid4().hex
    role = "oms_test_" + uuid.uuid4().hex
    script = Path(__file__).resolve().parents[1] / "scripts" / "render_fresh_sql.py"
    fresh = subprocess.run([sys.executable, str(script), "--schema", schema],
                           capture_output=True, text=True, check=True).stdout
    grants = (root / "infra/supabase/runtime_permissions.sql").read_text()
    grants = re.sub(r"\boms_runtime\b", role, grants)
    grants = re.sub(r"\boms\b", schema, grants)
    engine = sa.create_engine(base_url)
    try:
        with engine.connect() as c:
            c.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN')
            c.commit()
            c.exec_driver_sql(fresh)
            c.exec_driver_sql(grants)
            c.commit()
        with engine.begin() as c:
            c.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
            assert c.exec_driver_sql(f'SELECT count(*) FROM "{schema}".org_nodes').scalar_one() == 13
            assert c.exec_driver_sql(f'SELECT version_num FROM "{schema}".alembic_version').scalar_one() == "0005_personal_workspace"
            assert c.exec_driver_sql(f'UPDATE "{schema}".org_nodes SET name=name WHERE kind=\'THANA\'').rowcount == 1
        for statement in (
            f'DELETE FROM "{schema}".members',
            f'UPDATE "{schema}".member_events SET action=action',
            f'DELETE FROM "{schema}".audit_logs',
            f'TRUNCATE "{schema}".membership_deltas',
            f'CREATE TABLE "{schema}".forbidden (id integer)',
        ):
            with pytest.raises(sa.exc.DBAPIError, match="permission denied"):
                with engine.begin() as c:
                    c.exec_driver_sql(f'SET LOCAL ROLE "{role}"')
                    c.exec_driver_sql(statement)
    finally:
        with engine.begin() as c:
            c.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            c.exec_driver_sql(f'DROP OWNED BY "{role}"')
            c.exec_driver_sql(f'DROP ROLE "{role}"')
        engine.dispose()
