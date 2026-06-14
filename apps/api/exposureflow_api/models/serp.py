import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from exposureflow_api.models.base import Base, TimestampMixin, new_uuid


class SerpSlotTarget(Base, TimestampMixin):
    __tablename__ = "serp_slot_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exposure_opportunities.id"), nullable=True
    )
    topic_cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topic_clusters.id"), nullable=True
    )
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    slot_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_status: Mapped[str] = mapped_column(String(32), nullable=False, default="target")
    current_owner: Mapped[str | None] = mapped_column(String(32), nullable=True)
    current_owner_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
