import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from exposureflow_api.models.base import Base, TimestampMixin, new_uuid


class ExposureTheme(Base, TimestampMixin):
    __tablename__ = "exposure_themes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    parent_theme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exposure_themes.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)


class TopicCluster(Base, TimestampMixin):
    __tablename__ = "topic_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    exposure_theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exposure_themes.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    pillar_keyword: Mapped[str] = mapped_column(Text, nullable=False)
    pillar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverage_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    authority_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    total_impressions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    ai_visibility_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    last_analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class TopicNode(Base, TimestampMixin):
    __tablename__ = "topic_nodes"
    __table_args__ = (
        UniqueConstraint("workspace_id", "site_id", "keyword", name="uq_topic_node_keyword"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    topic_cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topic_clusters.id"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    keyword_level: Mapped[str] = mapped_column(String(16), nullable=False, default="mid_tail")
    search_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_best_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    exposure_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exposure_assets.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="gap")
    impressions: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    avg_position: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    cluster_assignment_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class CannibalizationCase(Base, TimestampMixin):
    __tablename__ = "cannibalization_cases"

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
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    competing_urls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class InternalLinkSuggestion(Base, TimestampMixin):
    __tablename__ = "internal_link_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    topic_cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topic_clusters.id"), nullable=False, index=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_text: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_relevance_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    approval_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
