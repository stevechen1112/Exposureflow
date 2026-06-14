"""Unique constraint for SERP slot targets."""

from alembic import op

revision = "008_serp_slot_target_unique"
down_revision = "007_ai_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_serp_slot_target_keyword_slot",
        "serp_slot_targets",
        ["workspace_id", "site_id", "keyword", "slot_type"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_serp_slot_target_keyword_slot", "serp_slot_targets", type_="unique")
