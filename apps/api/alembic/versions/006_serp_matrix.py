"""SERP slot target table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_serp_matrix"
down_revision = "005_topic_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "serp_slot_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_opportunities.id"), nullable=True),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic_clusters.id"), nullable=True),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("slot_type", sa.String(32), nullable=False),
        sa.Column("target_status", sa.String(32), nullable=False, server_default="target"),
        sa.Column("current_owner", sa.String(32), nullable=True),
        sa.Column("current_owner_url", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_serp_slot_targets_workspace_id", "serp_slot_targets", ["workspace_id"])
    op.create_index("ix_serp_slot_targets_site_keyword", "serp_slot_targets", ["site_id", "keyword"])


def downgrade() -> None:
    op.drop_table("serp_slot_targets")
