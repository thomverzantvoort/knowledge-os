import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.database.models.enums import (
    ContentItemKind,
    ProcessingStatus,
    TranscriptStatus,
)


class ContentItem(Base, TimestampMixin):
    __tablename__ = "content_items"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "external_id", name="uq_content_items_source_external"
        ),
        Index("ix_content_items_published_at", "published_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[ContentItemKind] = mapped_column(
        Enum(ContentItemKind, name="content_item_kind", native_enum=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(10000))
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    channel_title: Mapped[str | None] = mapped_column(String(512))
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    transcript_status: Mapped[TranscriptStatus] = mapped_column(
        Enum(TranscriptStatus, name="transcript_status", native_enum=True),
        nullable=False,
        default=TranscriptStatus.PENDING,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status", native_enum=True),
        nullable=False,
        default=ProcessingStatus.INGESTED,
    )
