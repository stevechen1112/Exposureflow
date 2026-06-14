"""Add pgvector embedding column to knowledge_facts."""

from alembic import op
import sqlalchemy as sa

revision = "012_knowledge_embeddings"
down_revision = "011_usage_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE knowledge_facts ADD COLUMN IF NOT EXISTS embedding vector(384)")


def downgrade() -> None:
    op.execute("ALTER TABLE knowledge_facts DROP COLUMN IF EXISTS embedding")
