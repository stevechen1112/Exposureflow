"""Normalize nullable GSC/Bing dimensions for reliable upsert uniqueness."""

from alembic import op
import sqlalchemy as sa

revision = "003_ingestion_unique_coalesce"
down_revision = "002_ingestion_layer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE gsc_performance_rows SET country = '' WHERE country IS NULL")
    op.execute("UPDATE gsc_performance_rows SET device = '' WHERE device IS NULL")
    op.execute("UPDATE bing_performance_rows SET country = '' WHERE country IS NULL")
    op.execute("UPDATE bing_performance_rows SET device = '' WHERE device IS NULL")

    op.alter_column(
        "gsc_performance_rows",
        "country",
        existing_type=sa.String(16),
        nullable=False,
        server_default="",
    )
    op.alter_column(
        "gsc_performance_rows",
        "device",
        existing_type=sa.String(16),
        nullable=False,
        server_default="",
    )
    op.alter_column(
        "bing_performance_rows",
        "country",
        existing_type=sa.String(16),
        nullable=False,
        server_default="",
    )
    op.alter_column(
        "bing_performance_rows",
        "device",
        existing_type=sa.String(16),
        nullable=False,
        server_default="",
    )


def downgrade() -> None:
    op.alter_column("bing_performance_rows", "device", nullable=True, server_default=None)
    op.alter_column("bing_performance_rows", "country", nullable=True, server_default=None)
    op.alter_column("gsc_performance_rows", "device", nullable=True, server_default=None)
    op.alter_column("gsc_performance_rows", "country", nullable=True, server_default=None)
