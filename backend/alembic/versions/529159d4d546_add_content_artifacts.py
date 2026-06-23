"""add_content_artifacts

Revision ID: 529159d4d546
Revises: 5ccd309c2a94
Create Date: 2026-06-23 11:49:28.131922

Tier 2 deep-dive output per content item: long narrative summary and
timestamped chapter outline. One row per item (unique on content_item_id).
Raw ingest text stays in content_bodies.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "529159d4d546"
down_revision: Union[str, Sequence[str], None] = "5ccd309c2a94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content_item_id", sa.Uuid(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("chapters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["content_item_id"],
            ["content_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "content_item_id",
            name="uq_content_artifacts_content_item",
        ),
    )


def downgrade() -> None:
    op.drop_table("content_artifacts")
