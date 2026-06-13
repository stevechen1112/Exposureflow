import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from exposureflow_api.models.base import Base, TimestampMixin, new_uuid


class IntegrationCredential(Base, TimestampMixin):
    __tablename__ = "integration_credentials"
    __table_args__ = (
        UniqueConstraint("workspace_id", "provider", "credential_name", name="uq_workspace_provider_cred"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_name: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    credential_type: Mapped[str] = mapped_column(String(32), nullable=False)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    workspace: Mapped["Workspace"] = relationship(back_populates="integration_credentials")  # noqa: F821
