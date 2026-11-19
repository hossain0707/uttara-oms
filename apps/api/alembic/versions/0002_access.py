"""Two-person role change requests.

Revision ID: 0002_access
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
revision = "0002_access"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("access_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("auth_sub", sa.String(128), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("scope_node_id", sa.Uuid(), sa.ForeignKey("org_nodes.id")),
        sa.Column("operation", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("requested_by", sa.Uuid(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("app_users.id")),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_table("access_requests")
