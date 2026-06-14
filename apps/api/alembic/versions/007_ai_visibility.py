"""AI visibility tables: probe sets, runs, citations, brand entity, SERPO."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_ai_visibility"
down_revision = "006_serp_matrix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_probe_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topic_clusters.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("prompts_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("surfaces_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("schedule", sa.String(64), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_probe_sets_workspace_id", "ai_probe_sets", ["workspace_id"])
    op.create_index("ix_ai_probe_sets_site_id", "ai_probe_sets", ["site_id"])

    op.create_table(
        "ai_probe_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("probe_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_probe_sets.id"), nullable=True),
        sa.Column("probe_mode", sa.String(32), nullable=False, server_default="assisted_manual"),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("surface", sa.String(64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("cited_urls_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("mentioned_brands_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("sentiment", sa.String(32), nullable=True),
        sa.Column("our_brand_mentioned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("our_url_cited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_url_cited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("competitor_mentions_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("raw_response_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_probe_runs_workspace_id", "ai_probe_runs", ["workspace_id"])
    op.create_index("ix_ai_probe_runs_site_id", "ai_probe_runs", ["site_id"])
    op.create_index("ix_ai_probe_runs_probe_set_id", "ai_probe_runs", ["probe_set_id"])

    op.create_table(
        "ai_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("ai_probe_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_probe_runs.id"), nullable=True),
        sa.Column("surface", sa.String(64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("cited_url", sa.Text(), nullable=False),
        sa.Column("cited_domain", sa.String(255), nullable=True),
        sa.Column("cited_title", sa.Text(), nullable=True),
        sa.Column("citation_context", sa.Text(), nullable=True),
        sa.Column("is_own_site", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_third_party_about_brand", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_competitor", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_citations_workspace_id", "ai_citations", ["workspace_id"])
    op.create_index("ix_ai_citations_site_id", "ai_citations", ["site_id"])

    op.create_table(
        "brand_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("canonical_name", sa.Text(), nullable=False),
        sa.Column("aliases_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("official_profiles_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("entity_consistency_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_brand_entities_workspace_id", "brand_entities", ["workspace_id"])
    op.create_index("ix_brand_entities_site_id", "brand_entities", ["site_id"])

    op.create_table(
        "brand_mentions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("ai_probe_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_probe_runs.id"), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_domain", sa.String(255), nullable=True),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="ai_answer"),
        sa.Column("mention_text", sa.Text(), nullable=False),
        sa.Column("linked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sentiment", sa.String(32), nullable=True),
        sa.Column("authority_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("relevance_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_brand_mentions_workspace_id", "brand_mentions", ["workspace_id"])
    op.create_index("ix_brand_mentions_site_id", "brand_mentions", ["site_id"])

    op.create_table(
        "serpo_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("brand_query", sa.Text(), nullable=False),
        sa.Column("keyword", sa.Text(), nullable=True),
        sa.Column("surface", sa.String(64), nullable=False, server_default="google"),
        sa.Column("first_page_positive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_page_neutral_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_page_negative_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_page_wrong_info_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommended_actions_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_serpo_records_workspace_id", "serpo_records", ["workspace_id"])
    op.create_index("ix_serpo_records_site_id", "serpo_records", ["site_id"])


def downgrade() -> None:
    op.drop_table("serpo_records")
    op.drop_table("brand_mentions")
    op.drop_table("brand_entities")
    op.drop_table("ai_citations")
    op.drop_table("ai_probe_runs")
    op.drop_table("ai_probe_sets")
