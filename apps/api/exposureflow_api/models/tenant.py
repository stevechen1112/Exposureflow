import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from exposureflow_api.models.base import Base, TimestampMixin, new_uuid


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    billing_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    organizations: Mapped[list["Organization"]] = relationship(back_populates="account")
    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="account")


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    account: Mapped[Account] = relationship(back_populates="organizations")
    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="organization")


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workspace_type: Mapped[str] = mapped_column(String(32), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    default_locale: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-TW")
    feature_flags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    plan_limits: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    usage_limits: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    account: Mapped[Account] = relationship(back_populates="workspaces")
    organization: Mapped[Organization] = relationship(back_populates="workspaces")
    memberships: Mapped[list["WorkspaceMembership"]] = relationship(back_populates="workspace")
    sites: Mapped[list["Site"]] = relationship(back_populates="workspace")
    integration_credentials: Mapped[list["IntegrationCredential"]] = relationship(  # noqa: F821
        back_populates="workspace"
    )
    invitations: Mapped[list["WorkspaceInvitation"]] = relationship(  # noqa: F821
        back_populates="workspace"
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(back_populates="user")


class WorkspaceMembership(Base, TimestampMixin):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships", foreign_keys=[user_id])


class Site(Base, TimestampMixin):
    __tablename__ = "sites"
    __table_args__ = (UniqueConstraint("workspace_id", "domain", name="uq_workspace_domain"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    site_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_locale: Mapped[str] = mapped_column(String(16), nullable=False, default="zh-TW")
    target_countries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    target_languages: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    business_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")

    workspace: Mapped[Workspace] = relationship(back_populates="sites")
