"""Business constraint rules table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "019_business_constraint_rules"
down_revision = "018_business_intake_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_constraint_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id"),
            nullable=False,
        ),
        sa.Column(
            "site_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sites.id"),
            nullable=False,
        ),
        sa.Column(
            "source_intake_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_intakes.id"),
            nullable=True,
        ),
        sa.Column("source_intake_version", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.Text(), nullable=False, server_default="substring"),
        sa.Column("match_pattern", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False, server_default="block"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.Text(), nullable=False, server_default="intake"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_business_constraint_rules_site_active",
        "business_constraint_rules",
        ["site_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_business_constraint_rules_site_active", table_name="business_constraint_rules")
    op.drop_table("business_constraint_rules")
