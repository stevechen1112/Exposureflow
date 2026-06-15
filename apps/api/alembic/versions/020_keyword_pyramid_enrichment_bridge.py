"""Keyword pyramid enrichment and topic graph bridge fields."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "020_keyword_pyramid_bridge"
down_revision = "019_business_constraint_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "keyword_pyramid_nodes",
        sa.Column("topic_node_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "keyword_pyramid_nodes",
        sa.Column("topic_cluster_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("keyword_pyramid_nodes", sa.Column("keyword_level", sa.Text(), nullable=True))
    op.add_column("keyword_pyramid_nodes", sa.Column("funnel_stage", sa.Text(), nullable=True))
    op.add_column(
        "keyword_pyramid_nodes",
        sa.Column("is_target", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_foreign_key(
        "fk_keyword_pyramid_nodes_topic_node_id",
        "keyword_pyramid_nodes",
        "topic_nodes",
        ["topic_node_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_keyword_pyramid_nodes_topic_cluster_id",
        "keyword_pyramid_nodes",
        "topic_clusters",
        ["topic_cluster_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_keyword_pyramid_nodes_topic_node",
        "keyword_pyramid_nodes",
        ["site_id", "topic_node_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_keyword_pyramid_nodes_topic_node", table_name="keyword_pyramid_nodes")
    op.drop_constraint(
        "fk_keyword_pyramid_nodes_topic_cluster_id",
        "keyword_pyramid_nodes",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_keyword_pyramid_nodes_topic_node_id",
        "keyword_pyramid_nodes",
        type_="foreignkey",
    )
    op.drop_column("keyword_pyramid_nodes", "is_target")
    op.drop_column("keyword_pyramid_nodes", "funnel_stage")
    op.drop_column("keyword_pyramid_nodes", "keyword_level")
    op.drop_column("keyword_pyramid_nodes", "topic_cluster_id")
    op.drop_column("keyword_pyramid_nodes", "topic_node_id")
