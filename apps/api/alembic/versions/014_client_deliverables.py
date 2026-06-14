"""Client deliverables: meeting notes, annotations, report delivery_mode."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "014_client_deliverables"
down_revision = "013_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("delivery_mode", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_reports_delivery_mode",
        "reports",
        "delivery_mode IS NULL OR delivery_mode IN "
        "('audit','roadmap','monthly_retainer','execution_tracker')",
    )

    op.create_table(
        "client_meeting_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("meeting_date", sa.Date(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("action_items_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_meeting_notes_workspace_id", "client_meeting_notes", ["workspace_id"])
    op.create_index("ix_client_meeting_notes_site_id", "client_meeting_notes", ["site_id"])

    op.create_table(
        "delivery_annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("roadmap_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roadmap_items.id"), nullable=True),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("annotation_type", sa.Text(), nullable=False, server_default="comment"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_delivery_annotations_workspace_id", "delivery_annotations", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("delivery_annotations")
    op.drop_table("client_meeting_notes")
    op.drop_constraint("ck_reports_delivery_mode", "reports", type_="check")
    op.drop_column("reports", "delivery_mode")
