"""Topic coverage graph tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_topic_graph"
down_revision = "004_exposure_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exposure_themes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("parent_theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_themes.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("business_priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_exposure_themes_workspace_id", "exposure_themes", ["workspace_id"])

    op.create_table(
        "topic_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("exposure_theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_themes.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("pillar_keyword", sa.Text(), nullable=False),
        sa.Column("pillar_url", sa.Text(), nullable=True),
        sa.Column("coverage_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("authority_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("total_impressions", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("ai_visibility_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_topic_clusters_workspace_id", "topic_clusters", ["workspace_id"])
    op.create_index("ix_topic_clusters_site_impressions", "topic_clusters", ["site_id", sa.text("total_impressions DESC")])

    op.create_table(
        "topic_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic_clusters.id"), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(32), nullable=True),
        sa.Column("keyword_level", sa.String(16), nullable=False, server_default="mid_tail"),
        sa.Column("search_context", sa.Text(), nullable=True),
        sa.Column("current_best_url", sa.Text(), nullable=True),
        sa.Column("exposure_asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_assets.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="gap"),
        sa.Column("impressions", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("avg_position", sa.Numeric(8, 3), nullable=True),
        sa.Column("cluster_assignment_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "site_id", "keyword", name="uq_topic_node_keyword"),
    )
    op.create_index("ix_topic_nodes_workspace_id", "topic_nodes", ["workspace_id"])
    op.create_index("ix_topic_nodes_cluster_id", "topic_nodes", ["topic_cluster_id"])
    op.create_index("ix_topic_nodes_site_status", "topic_nodes", ["site_id", "status"])

    op.create_table(
        "cannibalization_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic_clusters.id"), nullable=True),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.String(32), nullable=False),
        sa.Column("competing_urls", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_cannibalization_cases_workspace_id", "cannibalization_cases", ["workspace_id"])

    op.create_table(
        "internal_link_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic_clusters.id"), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("anchor_text", sa.Text(), nullable=False),
        sa.Column("anchor_relevance_score", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("approval_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_internal_link_suggestions_workspace_id", "internal_link_suggestions", ["workspace_id"])
    op.create_index("ix_internal_link_suggestions_cluster_id", "internal_link_suggestions", ["topic_cluster_id"])

    op.create_foreign_key(
        "fk_exposure_assets_topic_cluster",
        "exposure_assets",
        "topic_clusters",
        ["topic_cluster_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_exposure_assets_topic_cluster", "exposure_assets", type_="foreignkey")
    op.drop_table("internal_link_suggestions")
    op.drop_table("cannibalization_cases")
    op.drop_table("topic_nodes")
    op.drop_table("topic_clusters")
    op.drop_table("exposure_themes")
