"""Reports table for client deliverables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "013_reports"
down_revision = "012_knowledge_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column("report_type", sa.Text(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column("branding_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("storage_url", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reports_workspace_id", "reports", ["workspace_id"])
    op.create_index("ix_reports_site_id", "reports", ["site_id"])
    op.create_check_constraint(
        "ck_reports_report_type",
        "reports",
        "report_type IN ('monthly_exposure','audit','roadmap','client_summary')",
    )


def downgrade() -> None:
    op.drop_table("reports")
