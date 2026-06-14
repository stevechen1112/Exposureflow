"""Strategy intake, knowledge base, and execution plane foundation."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "010_strategy_knowledge_execution"
down_revision = "009_decision_plane"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_intakes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("company_summary", sa.Text(), nullable=True),
        sa.Column("market_notes", sa.Text(), nullable=True),
        sa.Column("customer_segments_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("domestic_markets_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("export_markets_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("sales_regions_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("strategic_goals_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("constraints_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_business_intakes_workspace_site", "business_intakes", ["workspace_id", "site_id"])

    op.create_table(
        "product_service_scopes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("scope_type", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_markets_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("target_personas_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("source", sa.String(32), nullable=False, server_default="consultant"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_product_service_scopes_workspace_site_status",
        "product_service_scopes",
        ["workspace_id", "site_id", "status"],
    )

    op.create_table(
        "keyword_pyramid_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("keyword_pyramid_nodes.id"), nullable=True),
        sa.Column(
            "product_service_scope_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_service_scopes.id"),
            nullable=True,
        ),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("intent", sa.String(32), nullable=True),
        sa.Column("target_market", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("business_fit_status", sa.String(32), nullable=False, server_default="in_scope"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_by", sa.String(32), nullable=False, server_default="consultant"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_keyword_pyramid_workspace_site_fit",
        "keyword_pyramid_nodes",
        ["workspace_id", "site_id", "business_fit_status"],
    )

    op.create_table(
        "delivery_commitments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("period", sa.String(16), nullable=False, server_default="monthly"),
        sa.Column("new_content_target", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refresh_target", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("faq_schema_target", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("technical_fix_target", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_target", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_delivery_commitments_workspace_site",
        "delivery_commitments",
        ["workspace_id", "site_id"],
    )

    op.create_table(
        "workspace_brand_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column("canonical_brand_name", sa.Text(), nullable=False),
        sa.Column("brand_voice_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("positioning_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("target_markets_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("buyer_personas_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("compliance_policy_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("default_review_policy", sa.String(32), nullable=False, server_default="editor_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workspace_brand_profiles_workspace", "workspace_brand_profiles", ["workspace_id"])

    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("market", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_knowledge_sources_workspace_site_status",
        "knowledge_sources",
        ["workspace_id", "site_id", "status"],
    )

    op.create_table(
        "knowledge_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=True),
        sa.Column(
            "knowledge_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_sources.id"),
            nullable=False,
        ),
        sa.Column("fact_type", sa.String(32), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.Column("market", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False, server_default="1.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_knowledge_facts_workspace_site_type_status",
        "knowledge_facts",
        ["workspace_id", "site_id", "fact_type", "status"],
    )

    op.create_table(
        "execution_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_decisions.id"), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_opportunities.id"), nullable=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("executor_type", sa.String(32), nullable=False, server_default="content_engine"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("input_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("output_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_execution_jobs_workspace_site_status", "execution_jobs", ["workspace_id", "site_id", "status"])

    op.create_table(
        "content_source_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_opportunities.id"), nullable=True),
        sa.Column("execution_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("execution_jobs.id"), nullable=True),
        sa.Column("market", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("required_coverage_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("source_refs_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("coverage_score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ready"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "content_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exposure_opportunities.id"), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("action_decisions.id"), nullable=True),
        sa.Column("source_pack_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_source_packs.id"), nullable=True),
        sa.Column("brief_type", sa.String(32), nullable=False),
        sa.Column("market", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("target_persona", sa.Text(), nullable=True),
        sa.Column("buyer_stage", sa.Text(), nullable=True),
        sa.Column("required_evidence_slots_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("forbidden_claims_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("brief_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "content_generation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("execution_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("execution_jobs.id"), nullable=False),
        sa.Column("content_brief_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_briefs.id"), nullable=False),
        sa.Column("generation_mode", sa.String(32), nullable=False),
        sa.Column("review_level", sa.String(32), nullable=False, server_default="editor"),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("input_hash", sa.Text(), nullable=False),
        sa.Column("output_markdown", sa.Text(), nullable=True),
        sa.Column("evidence_map_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("unsupported_claims_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "content_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column(
            "content_generation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_generation_runs.id"),
            nullable=False,
        ),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(32), nullable=False),
        sa.Column("source_refs_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("verification_status", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("finding_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "content_gate_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("execution_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("execution_jobs.id"), nullable=False),
        sa.Column(
            "content_generation_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_generation_runs.id"),
            nullable=True,
        ),
        sa.Column("gate_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("findings_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("content_gate_results")
    op.drop_table("content_claims")
    op.drop_table("content_generation_runs")
    op.drop_table("content_briefs")
    op.drop_table("content_source_packs")
    op.drop_table("execution_jobs")
    op.drop_table("knowledge_facts")
    op.drop_table("knowledge_sources")
    op.drop_table("workspace_brand_profiles")
    op.drop_table("delivery_commitments")
    op.drop_table("keyword_pyramid_nodes")
    op.drop_table("product_service_scopes")
    op.drop_table("business_intakes")
