"""Database race barriers and append-only accounting.

Revision ID: 0004_invariants
Revises: 0003_membership_ledger
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_invariants"
down_revision = "0003_membership_ledger"
branch_labels = None
depends_on = None


def upgrade():
    # Fail on legacy duplicates instead of deleting existing records.
    for name, table, columns, condition in (
        ("uq_org_single_thana", "org_nodes", ["kind"], "kind = 'THANA'"),
        ("uq_role_global", "role_grants", ["user_id", "role"], "scope_node_id IS NULL"),
        ("uq_pending_member_change", "change_requests", ["member_id", "kind"], "status = 'PENDING'"),
    ):
        op.create_index(name, table, columns, unique=True,
                        postgresql_where=sa.text(condition), sqlite_where=sa.text(condition))
    if op.get_bind().dialect.name == "postgresql":
        op.execute("""CREATE FUNCTION oms_reject_history_mutation() RETURNS trigger
                   LANGUAGE plpgsql AS $$ BEGIN
                   RAISE EXCEPTION 'OMS history is append-only'; END; $$""")
        for table in ("member_events", "membership_deltas", "audit_logs"):
            op.execute(f"CREATE TRIGGER oms_history_immutable BEFORE UPDATE OR DELETE ON {table} "
                       "FOR EACH ROW EXECUTE FUNCTION oms_reject_history_mutation()")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        for table in ("member_events", "membership_deltas", "audit_logs"):
            op.execute(f"DROP TRIGGER oms_history_immutable ON {table}")
        op.execute("DROP FUNCTION oms_reject_history_mutation()")
    op.drop_index("uq_pending_member_change", table_name="change_requests")
    op.drop_index("uq_role_global", table_name="role_grants")
    op.drop_index("uq_org_single_thana", table_name="org_nodes")
