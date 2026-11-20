"""Private personal profiles, explicit reviewer assignments and monthly reports."""

from alembic import op
import sqlalchemy as sa

revision = "0005_personal_workspace"
down_revision = "0004_invariants"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personal_profiles",
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("app_users.id"), primary_key=True
        ),
        sa.Column("details_encrypted", sa.Text()),
        sa.Column("goals_encrypted", sa.Text()),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("app_users.id")),
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id"), unique=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "personal_reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("content_encrypted", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("app_users.id")),
        sa.Column("review_note_encrypted", sa.Text()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "month", name="uq_personal_report_user_month"),
    )

    if op.get_context().dialect.name == "postgresql":
        op.execute("ALTER TABLE personal_profiles ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE personal_reports ENABLE ROW LEVEL SECURITY")


def downgrade():
    op.drop_table("personal_reports")
    op.drop_table("personal_profiles")
