from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models.content_artifact import ContentArtifact
from app.database.models.content_body import ContentBody
from app.database.models.content_item import ContentItem
from app.database.models.enums import BodyKind, BodyStatus, ProcessingStatus, UserStatus


def load_artifact(session: Session, item_id: UUID) -> ContentArtifact | None:
    return session.scalar(
        select(ContentArtifact).where(ContentArtifact.content_item_id == item_id)
    )


def artifact_is_complete(artifact: ContentArtifact | None) -> bool:
    if artifact is None:
        return False
    return artifact.chapters is not None and artifact.summary is not None


def items_needing_deep(session: Session) -> list[ContentItem]:
    query = (
        select(ContentItem)
        .outerjoin(
            ContentArtifact,
            ContentArtifact.content_item_id == ContentItem.id,
        )
        .where(ContentItem.user_status == UserStatus.INTERESTED)
        .where(
            or_(
                ContentArtifact.id.is_(None),
                ContentArtifact.chapters.is_(None),
                ContentArtifact.summary.is_(None),
            )
        )
        .order_by(ContentItem.published_at.desc())
    )
    return list(session.scalars(query).all())


def save_artifact(
    session: Session,
    item_id: UUID,
    *,
    chapters: list,
    summary: dict,
    model: str,
    generated_at: datetime,
) -> ContentArtifact:
    artifact = load_artifact(session, item_id)
    if artifact is None:
        artifact = ContentArtifact(
            content_item_id=item_id,
            chapters=chapters,
            summary=summary,
            model=model,
            generated_at=generated_at,
        )
        session.add(artifact)
    else:
        artifact.chapters = chapters
        artifact.summary = summary
        artifact.model = model
        artifact.generated_at = generated_at
    return artifact


def mark_deep_failed(session: Session, item: ContentItem) -> None:
    item.processing_status = ProcessingStatus.FAILED


def reset_processing_status(session: Session, item: ContentItem) -> None:
    item.processing_status = ProcessingStatus.INGESTED


def load_transcript_body(session: Session, item_id: UUID) -> ContentBody | None:
    return session.scalar(
        select(ContentBody).where(
            ContentBody.content_item_id == item_id,
            ContentBody.body_kind == BodyKind.TRANSCRIPT,
        )
    )


def transcript_is_available(item: ContentItem, body: ContentBody | None) -> bool:
    if item.body_status != BodyStatus.AVAILABLE:
        return False
    if body is None or not body.snippets:
        return False
    return True
