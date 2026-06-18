"""022 — ops health runs and signals for AI maintenance engineer."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "022_ops_health_runs"
down_revision = "021_content_schedules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ops_health_runs" in inspector.get_table_names():
        return

    op.create_table(
        "ops_health_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("trigger", sa.String(32), nullable=False, server_default="scheduled"),
        sa.Column("summary_title", sa.Text(), nullable=True),
        sa.Column("summary_markdown", sa.Text(), nullable=True),
        sa.Column("llm_provider", sa.String(32), nullable=True),
        sa.Column("llm_model", sa.String(64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("ix_ops_health_runs_started_at", "ops_health_runs", ["started_at"])

    op.create_table(
        "ops_health_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ops_health_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("check_id", sa.String(128), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("action_type", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ops_health_signals_run_id", "ops_health_signals", ["run_id"])
    op.create_index("ix_ops_health_signals_severity", "ops_health_signals", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_ops_health_signals_severity", table_name="ops_health_signals")
    op.drop_index("ix_ops_health_signals_run_id", table_name="ops_health_signals")
    op.drop_table("ops_health_signals")
    op.drop_index("ix_ops_health_runs_started_at", table_name="ops_health_runs")
    op.drop_table("ops_health_runs")
