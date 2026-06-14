"""Exposure core tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_exposure_core"
down_revision = "003_ingestion_unique_coalesce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exposure_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asset_type", sa.String(32), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("primary_keyword", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_impressions", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_clicks", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("ai_citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("serp_slot_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "site_id", "url", name="uq_exposure_asset_url"),
    )
    op.create_index("ix_exposure_assets_workspace_id", "exposure_assets", ["workspace_id"])
    op.create_index("ix_exposure_assets_site_id", "exposure_assets", ["site_id"])

    op.create_table(
        "exposure_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exposure_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_assets.id"), nullable=True),
        sa.Column("opportunity_type", sa.String(64), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=True),
        sa.Column("search_context", sa.Text(), nullable=True),
        sa.Column("target_url", sa.Text(), nullable=True),
        sa.Column("current_url", sa.Text(), nullable=True),
        sa.Column("current_impressions", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("current_position", sa.Numeric(6, 2), nullable=True),
        sa.Column("ranking_feasibility_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("serp_slot_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("ai_citation_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("topic_contribution_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("zero_click_value_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("total_opportunity_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_exposure_opportunities_workspace_id", "exposure_opportunities", ["workspace_id"])
    op.create_index("ix_exposure_opportunities_site_id", "exposure_opportunities", ["site_id"])
    op.create_index(
        "ix_exposure_opportunities_site_score",
        "exposure_opportunities",
        ["site_id", sa.text("total_opportunity_score DESC")],
    )

    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("aliases_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "site_id", "domain", name="uq_competitor_domain"),
    )
    op.create_index("ix_competitors_workspace_id", "competitors", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("competitors")
    op.drop_table("exposure_opportunities")
    op.drop_table("exposure_assets")
