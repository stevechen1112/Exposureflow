"""021 — content_schedules table for automated batch generation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "021_content_schedules"
down_revision = "020_keyword_pyramid_bridge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "content_schedules" in inspector.get_table_names():
        return

    op.create_table(
        "content_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("articles_per_week", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("priority_filter", sa.String(16), nullable=False, server_default="P1"),
        sa.Column(
            "schedule_days_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[\"mon\", \"thu\"]'::jsonb"),
        ),
        sa.Column("auto_approve_threshold", sa.Integer(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_content_schedules_workspace_id", "content_schedules", ["workspace_id"])
    op.create_index("ix_content_schedules_site_id", "content_schedules", ["site_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_content_schedules_site_id", table_name="content_schedules")
    op.drop_index("ix_content_schedules_workspace_id", table_name="content_schedules")
    op.drop_table("content_schedules")
