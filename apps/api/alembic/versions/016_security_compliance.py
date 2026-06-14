"""Security settings, security events, and data export requests."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "016_security_compliance"
down_revision = "015_billing_commercial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_security_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False, unique=True),
        sa.Column("require_2fa", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sso_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("saml_entity_id", sa.Text(), nullable=True),
        sa.Column("saml_sso_url", sa.Text(), nullable=True),
        sa.Column("saml_certificate_encrypted", sa.Text(), nullable=True),
        sa.Column("ip_allowlist", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("deletion_status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="info"),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_security_events_workspace_id", "security_events", ["workspace_id"])
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])

    op.create_table(
        "data_export_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("export_json", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_data_export_requests_workspace_id", "data_export_requests", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("data_export_requests")
    op.drop_table("security_events")
    op.drop_table("workspace_security_settings")
