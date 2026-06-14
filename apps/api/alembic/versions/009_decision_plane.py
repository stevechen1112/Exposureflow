"""Decision plane tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009_decision_plane"
down_revision = "008_serp_slot_target_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "action_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_opportunities.id"), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("target_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_assets.id"), nullable=True),
        sa.Column("action_payload_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("expected_exposure_impact", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("required_inputs_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_by", sa.String(16), nullable=False, server_default="rule"),
        sa.Column("decision_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("rank_score", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_action_candidates_workspace_id", "action_candidates", ["workspace_id"])
    op.create_index("ix_action_candidates_site_id", "action_candidates", ["site_id"])
    op.create_index("ix_action_candidates_opportunity_id", "action_candidates", ["opportunity_id"])
    op.create_unique_constraint(
        "uq_action_candidate_opportunity",
        "action_candidates",
        ["workspace_id", "site_id", "opportunity_id"],
    )

    op.create_table(
        "action_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_candidates.id"), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("selected_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("scheduled_for", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_action_decisions_workspace_id", "action_decisions", ["workspace_id"])
    op.create_index("ix_action_decisions_candidate_id", "action_decisions", ["candidate_id"])

    op.create_table(
        "roadmaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("horizon_weeks", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_roadmaps_workspace_id", "roadmaps", ["workspace_id"])
    op.create_index("ix_roadmaps_site_id", "roadmaps", ["site_id"])

    op.create_table(
        "roadmap_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("roadmap_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roadmaps.id"), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_decisions.id"), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_candidates.id"), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("client_approval_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("expected_exposure_impact", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("dependency_item_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_roadmap_items_roadmap_id", "roadmap_items", ["roadmap_id"])
    op.create_index("ix_roadmap_items_site_id", "roadmap_items", ["site_id"])


def downgrade() -> None:
    op.drop_table("roadmap_items")
    op.drop_table("roadmaps")
    op.drop_table("action_decisions")
    op.drop_table("action_candidates")
