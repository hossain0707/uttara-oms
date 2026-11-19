"""Historical membership ledger; reconstruct legacy transitions without duplicating people.

Revision ID: 0003_membership_ledger
Revises: 0002_access
"""
import uuid
from collections import Counter
from alembic import op
import sqlalchemy as sa

revision = "0003_membership_ledger"
down_revision = "0002_access"
branch_labels = None
depends_on = None


def upgrade():
    ledger = op.create_table(
        "membership_deltas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_id", sa.Uuid(), sa.ForeignKey("member_events.id"), nullable=False),
        sa.Column("org_node_id", sa.Uuid(), sa.ForeignKey("org_nodes.id"), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("delta IN (-1, 1)", name="ck_membership_delta_sign"),
        sa.CheckConstraint("category IN ('RUKON', 'WORKER', 'ASSOCIATE', 'SUPPORTER')", name="ck_membership_delta_category"),
        sa.UniqueConstraint("event_id", "org_node_id", "category", name="uq_membership_delta_event_scope"),
    )
    op.create_index("ix_membership_delta_scope_time", "membership_deltas", ["org_node_id", "occurred_at"])
    connection = op.get_bind()
    members = sa.table("members", sa.column("id", sa.Uuid()), sa.column("org_node_id", sa.Uuid()),
                       sa.column("category", sa.String()), sa.column("status", sa.String()))
    events = sa.table("member_events", sa.column("id", sa.Uuid()), sa.column("member_id", sa.Uuid()),
                      sa.column("action", sa.String()), sa.column("before", sa.String()),
                      sa.column("after", sa.String()), sa.column("created_at", sa.DateTime(timezone=True)))
    # Invert complete legacy histories starting from authoritative current state.
    # Stop on incomplete/inconsistent data instead of inventing official history.
    for member in connection.execute(sa.select(members)).mappings():
        state = (member["org_node_id"], member["category"], member["status"])
        history = connection.execute(sa.select(events).where(events.c.member_id == member["id"])
                                     .order_by(events.c.created_at.desc(), events.c.id.desc())).mappings().all()
        created = False
        inserts = []
        for event in history:
            kind = event["action"]
            if kind == "ROUTINE_UPDATED":
                continue
            if created:
                raise RuntimeError("Legacy event precedes creation; repair history before migration")
            if kind == "CREATED":
                before = None
                created = True
                if state[2] != "ACTIVE":
                    raise RuntimeError("Inconsistent legacy creation state")
            elif kind == "CATEGORY":
                if event["after"] != state[1] or not event["before"]:
                    raise RuntimeError("Inconsistent legacy category history")
                before = (state[0], event["before"], state[2])
            elif kind == "TRANSFER":
                if event["after"] != str(state[0]) or not event["before"]:
                    raise RuntimeError("Inconsistent legacy transfer history")
                before = (uuid.UUID(event["before"]), state[1], state[2])
            elif kind in {"DEACTIVATE", "REACTIVATE"}:
                if event["after"] != state[2] or event["before"] not in {"ACTIVE", "INACTIVE"}:
                    raise RuntimeError("Inconsistent legacy status history")
                before = (state[0], state[1], event["before"])
            else:
                raise RuntimeError("Unknown legacy membership event; review before migration")
            delta = Counter()
            if before and before[2] == "ACTIVE":
                delta[(before[0], before[1])] -= 1
            if state[2] == "ACTIVE":
                delta[(state[0], state[1])] += 1
            inserts.extend(dict(id=uuid.uuid4(), event_id=event["id"], org_node_id=unit,
                                category=category, delta=value, occurred_at=event["created_at"])
                           for (unit, category), value in delta.items() if value)
            state = before
        if not created:
            raise RuntimeError("Missing legacy creation event; repair history before migration")
        if inserts:
            connection.execute(ledger.insert(), inserts)


def downgrade():
    op.drop_index("ix_membership_delta_scope_time", table_name="membership_deltas")
    op.drop_table("membership_deltas")
