"""Ingestion layer tables for GSC, GA4, SERP, Bing, Tech SEO."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_ingestion_layer"
down_revision = "001_initial_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_sync_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("cursor_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "site_id", "provider", name="uq_sync_state"),
    )
    op.create_index("ix_integration_sync_states_workspace_id", "integration_sync_states", ["workspace_id"])

    op.create_table(
        "gsc_performance_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("page", sa.Text(), nullable=False),
        sa.Column("country", sa.String(16), nullable=True),
        sa.Column("device", sa.String(16), nullable=True),
        sa.Column("impressions", sa.BigInteger(), nullable=False),
        sa.Column("clicks", sa.BigInteger(), nullable=False),
        sa.Column("ctr", sa.Numeric(8, 6), nullable=False),
        sa.Column("position", sa.Numeric(8, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("site_id", "date", "query", "page", "country", "device", name="uq_gsc_row"),
    )
    op.create_index("ix_gsc_performance_rows_workspace_id", "gsc_performance_rows", ["workspace_id"])
    op.create_index("ix_gsc_performance_rows_site_id", "gsc_performance_rows", ["site_id"])

    op.create_table(
        "ga4_page_metrics",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("page_path", sa.Text(), nullable=False),
        sa.Column("sessions", sa.BigInteger(), nullable=False),
        sa.Column("engaged_sessions", sa.BigInteger(), nullable=False),
        sa.Column("engagement_rate", sa.Numeric(8, 6), nullable=False),
        sa.Column("conversions", sa.Numeric(12, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("site_id", "date", "page_path", name="uq_ga4_page"),
    )
    op.create_index("ix_ga4_page_metrics_workspace_id", "ga4_page_metrics", ["workspace_id"])
    op.create_index("ix_ga4_page_metrics_site_id", "ga4_page_metrics", ["site_id"])

    op.create_table(
        "bing_performance_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("page", sa.Text(), nullable=False),
        sa.Column("country", sa.String(16), nullable=True),
        sa.Column("device", sa.String(16), nullable=True),
        sa.Column("impressions", sa.BigInteger(), nullable=False),
        sa.Column("clicks", sa.BigInteger(), nullable=False),
        sa.Column("ctr", sa.Numeric(8, 6), nullable=False),
        sa.Column("position", sa.Numeric(8, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("site_id", "date", "query", "page", "country", "device", name="uq_bing_row"),
    )
    op.create_index("ix_bing_performance_rows_workspace_id", "bing_performance_rows", ["workspace_id"])
    op.create_index("ix_bing_performance_rows_site_id", "bing_performance_rows", ["site_id"])

    op.create_table(
        "serp_query_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("surface", sa.String(32), nullable=False, server_default="google"),
        sa.Column("country", sa.String(16), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("device", sa.String(16), nullable=False),
        sa.Column("raw_provider", sa.String(32), nullable=False),
        sa.Column("raw_json", postgresql.JSONB(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_serp_query_snapshots_workspace_id", "serp_query_snapshots", ["workspace_id"])
    op.create_index("ix_serp_query_snapshots_site_id", "serp_query_snapshots", ["site_id"])

    op.create_table(
        "serp_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("serp_query_snapshots.id"), nullable=False),
        sa.Column("slot_type", sa.String(32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("owner_domain", sa.String(255), nullable=True),
        sa.Column("owner_brand", sa.String(255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("is_own_site", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_competitor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_third_party", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_serp_slots_workspace_id", "serp_slots", ["workspace_id"])
    op.create_index("ix_serp_slots_snapshot_id", "serp_slots", ["snapshot_id"])

    op.create_table(
        "technical_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("exposure_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("issue_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("source", sa.String(32), nullable=False, server_default="crawler"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fixed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_technical_issues_workspace_id", "technical_issues", ["workspace_id"])
    op.create_index("ix_technical_issues_site_id", "technical_issues", ["site_id"])


def downgrade() -> None:
    op.drop_table("technical_issues")
    op.drop_table("serp_slots")
    op.drop_table("serp_query_snapshots")
    op.drop_table("bing_performance_rows")
    op.drop_table("ga4_page_metrics")
    op.drop_table("gsc_performance_rows")
    op.drop_table("integration_sync_states")
