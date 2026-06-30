"""content_artifacts_summary_jsonb

Revision ID: 2a4b6c8d0e1f
Revises: 8f3a2b1c4d5e
Create Date: 2026-06-30 14:00:00.000000

Store structured SummaryResult JSON in content_artifacts.summary (JSONB).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "2a4b6c8d0e1f"
down_revision: Union[str, Sequence[str], None] = "8f3a2b1c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "content_artifacts",
        "summary",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using="summary::jsonb",
    )


def downgrade() -> None:
    op.alter_column(
        "content_artifacts",
        "summary",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="summary::text",
    )
