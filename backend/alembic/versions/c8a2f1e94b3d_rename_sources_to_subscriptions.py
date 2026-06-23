"""rename sources to subscriptions

Revision ID: c8a2f1e94b3d
Revises: b53116d551c5
Create Date: 2026-06-18 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c8a2f1e94b3d"
down_revision: Union[str, Sequence[str], None] = "b53116d551c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "content_items_source_id_fkey", "content_items", type_="foreignkey"
    )
    op.drop_constraint(
        "uq_content_items_source_external", "content_items", type_="unique"
    )

    op.alter_column(
        "content_items",
        "thumbnail_url",
        existing_type=sa.String(length=2048),
        nullable=True,
    )
    op.alter_column(
        "content_items",
        "source_id",
        new_column_name="subscription_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.alter_column(
        "content_items",
        "channel_title",
        new_column_name="author",
        existing_type=sa.String(length=512),
        existing_nullable=True,
    )
    op.alter_column(
        "content_items",
        "transcript_status",
        new_column_name="body_status",
        existing_type=sa.Enum(
            "PENDING",
            "AVAILABLE",
            "UNAVAILABLE",
            name="transcript_status",
        ),
        existing_nullable=False,
    )

    op.rename_table("sources", "subscriptions")

    op.create_foreign_key(
        "content_items_subscription_id_fkey",
        "content_items",
        "subscriptions",
        ["subscription_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_content_items_subscription_external",
        "content_items",
        ["subscription_id", "external_id"],
    )

    op.add_column(
        "subscriptions",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute("ALTER TYPE source_kind RENAME TO subscription_kind")
    op.execute("ALTER TYPE transcript_status RENAME TO body_status")
    op.execute("ALTER TYPE content_item_kind RENAME TO content_kind")


def downgrade() -> None:
    op.execute("ALTER TYPE content_kind RENAME TO content_item_kind")
    op.execute("ALTER TYPE body_status RENAME TO transcript_status")
    op.execute("ALTER TYPE subscription_kind RENAME TO source_kind")

    op.drop_column("subscriptions", "last_synced_at")

    op.drop_constraint(
        "uq_content_items_subscription_external", "content_items", type_="unique"
    )
    op.drop_constraint(
        "content_items_subscription_id_fkey", "content_items", type_="foreignkey"
    )

    op.rename_table("subscriptions", "sources")

    op.alter_column(
        "content_items",
        "body_status",
        new_column_name="transcript_status",
        existing_type=sa.Enum(
            "PENDING",
            "AVAILABLE",
            "UNAVAILABLE",
            name="body_status",
        ),
        existing_nullable=False,
    )
    op.alter_column(
        "content_items",
        "author",
        new_column_name="channel_title",
        existing_type=sa.String(length=512),
        existing_nullable=True,
    )
    op.alter_column(
        "content_items",
        "subscription_id",
        new_column_name="source_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.alter_column(
        "content_items",
        "thumbnail_url",
        existing_type=sa.String(length=2048),
        nullable=False,
    )

    op.create_foreign_key(
        "content_items_source_id_fkey",
        "content_items",
        "sources",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_content_items_source_external",
        "content_items",
        ["source_id", "external_id"],
    )
