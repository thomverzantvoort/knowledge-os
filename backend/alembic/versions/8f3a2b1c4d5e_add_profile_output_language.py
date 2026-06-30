"""add_profile_output_language

Revision ID: 8f3a2b1c4d5e
Revises: 529159d4d546
Create Date: 2026-06-30 12:00:00.000000

User preference for deep-processing output language: en, nl, or content.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8f3a2b1c4d5e"
down_revision: Union[str, Sequence[str], None] = "529159d4d546"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

output_language_enum = sa.Enum(
    "EN",
    "NL",
    "CONTENT",
    name="output_language",
)


def upgrade() -> None:
    output_language_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "user_interest_profiles",
        sa.Column(
            "output_language",
            output_language_enum,
            nullable=False,
            server_default=sa.text("'CONTENT'::output_language"),
        ),
    )
    op.alter_column("user_interest_profiles", "output_language", server_default=None)


def downgrade() -> None:
    op.drop_column("user_interest_profiles", "output_language")
    output_language_enum.drop(op.get_bind(), checkfirst=True)
