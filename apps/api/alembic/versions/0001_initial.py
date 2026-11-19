"""Initial OMS schema with scoped roles, consent, approval and audit tables.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("org_nodes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("org_nodes.id")),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("parent_id", "code", name="uq_org_parent_code"))
    op.create_table("app_users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("auth_sub", sa.String(128), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("role_grants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("scope_node_id", sa.Uuid(), sa.ForeignKey("org_nodes.id")),
        sa.UniqueConstraint("user_id", "role", "scope_node_id", name="uq_role_scope"))
    op.create_table("members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("member_number", sa.String(48), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("father_name", sa.String(200)),
        sa.Column("phone_encrypted", sa.Text()),
        sa.Column("phone_digest", sa.String(64), unique=True),
        sa.Column("address_encrypted", sa.Text()),
        sa.Column("occupation", sa.String(160)),
        sa.Column("position", sa.String(160)),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("org_node_id", sa.Uuid(), sa.ForeignKey("org_nodes.id"), nullable=False),
        sa.Column("joined_on", sa.Date()),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consent_version", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_members_scope_status_category", "members", ["org_node_id", "status", "category"])
    op.create_table("change_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("proposed_value", sa.String(128), nullable=False),
        sa.Column("original_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("app_users.id")),
        sa.Column("review_note", sa.String(300)),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.create_table("member_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("before", sa.String(128)),
        sa.Column("after", sa.String(128)),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_member_events_created", "member_events", ["created_at"])
    op.create_table("audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("action", sa.String(72), nullable=False),
        sa.Column("target_id", sa.String(40), nullable=False),
        sa.Column("detail", sa.String(250), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table("audit_logs")
    op.drop_index("ix_member_events_created", table_name="member_events")
    op.drop_table("member_events")
    op.drop_table("change_requests")
    op.drop_index("ix_members_scope_status_category", table_name="members")
    op.drop_table("members")
    op.drop_table("role_grants")
    op.drop_table("app_users")
    op.drop_table("org_nodes")
