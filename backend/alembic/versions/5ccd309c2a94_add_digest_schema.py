"""add_digest_schema

Revision ID: 5ccd309c2a94
Revises: c8a2f1e94b3d
Create Date: 2026-06-23 11:30:11.202435

Adds digest/triage schema: user_interest_profiles, content_items enrichment
columns, composite unique on content_bodies, and summary_deep body_kind value.

Note: body_kind enum values cannot be removed on downgrade (PostgreSQL limitation).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "5ccd309c2a94"
down_revision: Union[str, Sequence[str], None] = "c8a2f1e94b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_status_enum = sa.Enum(
    "UNREAD",
    "INTERESTED",
    "DISMISSED",
    name="user_status",
)


def upgrade() -> None:
    op.create_table(
        "user_interest_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "domain_weights",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("context_prose", sa.Text(), nullable=True),
        sa.Column("channel_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.execute(
        "ALTER TYPE body_kind ADD VALUE IF NOT EXISTS 'SUMMARY_DEEP'"
    )

    op.drop_constraint(
        op.f("content_bodies_content_item_id_key"),
        "content_bodies",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_content_bodies_item_kind",
        "content_bodies",
        ["content_item_id", "body_kind"],
    )

    user_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "content_items",
        sa.Column(
            "user_status",
            user_status_enum,
            nullable=False,
            server_default=sa.text("'UNREAD'::user_status"),
        ),
    )
    op.alter_column("content_items", "user_status", server_default=None)

    op.add_column(
        "content_items",
        sa.Column("enrichment", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_items", "enrichment")
    op.drop_column("content_items", "user_status")
    user_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_constraint(
        "uq_content_bodies_item_kind",
        "content_bodies",
        type_="unique",
    )
    op.create_unique_constraint(
        op.f("content_bodies_content_item_id_key"),
        "content_bodies",
        ["content_item_id"],
        postgresql_nulls_not_distinct=False,
    )

    op.drop_table("user_interest_profiles")
