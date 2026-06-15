"""Business intake versioning fields."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "018_business_intake_versions"
down_revision = "017_product_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "business_intakes",
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "business_intakes",
        sa.Column(
            "parent_intake_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("business_intakes.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "business_intakes",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "business_intakes",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "business_intakes",
        sa.Column("change_summary", sa.Text(), nullable=True),
    )

    # Backfill: assign version numbers per site by created_at.
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY site_id ORDER BY created_at ASC
                   ) AS rn
            FROM business_intakes
        )
        UPDATE business_intakes bi
        SET version_number = ranked.rn
        FROM ranked
        WHERE bi.id = ranked.id
        """
    )

    # Mark latest approved row per site as current.
    op.execute(
        """
        WITH latest_approved AS (
            SELECT DISTINCT ON (site_id) id
            FROM business_intakes
            WHERE status = 'approved'
            ORDER BY site_id, approved_at DESC NULLS LAST, created_at DESC
        )
        UPDATE business_intakes
        SET is_current = true
        WHERE id IN (SELECT id FROM latest_approved)
        """
    )

    # Archive older approved rows.
    op.execute(
        """
        UPDATE business_intakes
        SET status = 'archived',
            archived_at = COALESCE(archived_at, updated_at, created_at)
        WHERE status = 'approved'
          AND is_current = false
        """
    )

    op.create_index(
        "ix_business_intakes_site_current",
        "business_intakes",
        ["site_id"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_business_intakes_site_current", table_name="business_intakes")
    op.drop_column("business_intakes", "change_summary")
    op.drop_column("business_intakes", "archived_at")
    op.drop_column("business_intakes", "is_current")
    op.drop_column("business_intakes", "parent_intake_id")
    op.drop_column("business_intakes", "version_number")
