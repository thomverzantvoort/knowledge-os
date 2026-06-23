from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.content_body import ContentBody
from app.database.models.content_item import ContentItem
from app.database.models.enums import (
    BodyKind,
    BodyStatus,
    ContentKind,
    ProcessingStatus,
)


class ContentItemDraft(BaseModel):
    external_id: str
    kind: ContentKind
    title: str
    description: str | None = None
    url: str
    thumbnail_url: str | None = None
    author: str | None = None
    published_at: datetime


class BodyDraft(BaseModel):
    body_kind: BodyKind
    text: str | None = None
    snippets: list[dict] | None = None
    language_code: str | None = None
    is_generated: bool | None = None


def needs_body_fetch(item: ContentItem) -> bool:
    return item.body_status in (BodyStatus.PENDING, BodyStatus.UNAVAILABLE)


def ensure_content_item(
    session: Session,
    subscription_id,
    draft: ContentItemDraft,
) -> tuple[ContentItem, bool]:
    item = session.scalar(
        select(ContentItem).where(
            ContentItem.subscription_id == subscription_id,
            ContentItem.external_id == draft.external_id,
        )
    )
    if item is not None:
        return item, False

    item = ContentItem(
        subscription_id=subscription_id,
        external_id=draft.external_id,
        kind=draft.kind,
        title=draft.title,
        description=draft.description,
        url=draft.url,
        thumbnail_url=draft.thumbnail_url,
        author=draft.author,
        published_at=draft.published_at,
        body_status=BodyStatus.PENDING,
        processing_status=ProcessingStatus.INGESTED,
    )
    session.add(item)
    return item, True


def _get_or_create_body(session: Session, item: ContentItem) -> ContentBody:
    body = session.scalar(
        select(ContentBody).where(ContentBody.content_item_id == item.id)
    )
    if body is None:
        body = ContentBody(
            content_item_id=item.id,
            body_kind=BodyKind.TRANSCRIPT,
            fetched_at=datetime.now(timezone.utc),
        )
        session.add(body)
    return body


def save_body(session: Session, item: ContentItem, body: BodyDraft) -> None:
    content_body = _get_or_create_body(session, item)
    content_body.body_kind = body.body_kind
    content_body.text = body.text
    content_body.snippets = body.snippets
    content_body.language_code = body.language_code
    content_body.is_generated = body.is_generated
    content_body.error = None
    content_body.fetched_at = datetime.now(timezone.utc)
    item.body_status = BodyStatus.AVAILABLE


def mark_body_unavailable(
    session: Session,
    item: ContentItem,
    body_kind: BodyKind,
    error: str,
) -> None:
    content_body = _get_or_create_body(session, item)
    content_body.body_kind = body_kind
    content_body.error = error
    content_body.fetched_at = datetime.now(timezone.utc)
    item.body_status = BodyStatus.UNAVAILABLE
