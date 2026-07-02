"""add_processing_status_failed

Revision ID: 3c5d7e9f1a2b
Revises: 2a4b6c8d0e1f
Create Date: 2026-06-30 16:00:00.000000

Add failed value to processing_status for Tier 2 deep job errors.
ALTER TYPE ADD VALUE cannot be rolled back once committed.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "3c5d7e9f1a2b"
down_revision: Union[str, Sequence[str], None] = "2a4b6c8d0e1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'FAILED'"
    )


def downgrade() -> None:
    pass
