import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from exposureflow_api.models.base import Base, TimestampMixin, new_uuid


class AIProbeSet(Base, TimestampMixin):
    __tablename__ = "ai_probe_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    topic_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topic_clusters.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    prompts_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    surfaces_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    schedule: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AIProbeRun(Base):
    __tablename__ = "ai_probe_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    probe_set_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_probe_sets.id"), nullable=True, index=True
    )
    probe_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="assisted_manual")
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    surface: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    cited_urls_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    mentioned_brands_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    our_brand_mentioned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    our_url_cited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_url_cited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    competitor_mentions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_response_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AICitation(Base):
    __tablename__ = "ai_citations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    ai_probe_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_probe_runs.id"), nullable=True, index=True
    )
    surface: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    cited_url: Mapped[str] = mapped_column(Text, nullable=False)
    cited_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cited_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_own_site: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_third_party_about_brand: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_competitor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BrandEntity(Base, TimestampMixin):
    __tablename__ = "brand_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_profiles_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    entity_consistency_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)


class BrandMention(Base):
    __tablename__ = "brand_mentions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    ai_probe_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_probe_runs.id"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ai_answer")
    mention_text: Mapped[str] = mapped_column(Text, nullable=False)
    linked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    authority_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    relevance_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SerpoRecord(Base):
    __tablename__ = "serpo_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    brand_query: Mapped[str] = mapped_column(Text, nullable=False)
    keyword: Mapped[str | None] = mapped_column(Text, nullable=True)
    surface: Mapped[str] = mapped_column(String(64), nullable=False, default="google")
    first_page_positive_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_page_neutral_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_page_negative_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_page_wrong_info_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommended_actions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
