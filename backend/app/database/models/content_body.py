import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.database.models.enums import BodyKind


class ContentBody(Base, TimestampMixin):
    __tablename__ = "content_bodies"
    __table_args__ = (
        UniqueConstraint(
            "content_item_id",
            "body_kind",
            name="uq_content_bodies_item_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    body_kind: Mapped[BodyKind] = mapped_column(
        Enum(BodyKind, name="body_kind", native_enum=True),
        nullable=False,
    )
    language_code: Mapped[str | None] = mapped_column(String(16))
    is_generated: Mapped[bool | None] = mapped_column(Boolean)
    text: Mapped[str | None] = mapped_column(Text)
    snippets: Mapped[list | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
