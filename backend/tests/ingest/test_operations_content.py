import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.database.models.content_item import ContentItem
from app.database.models.enums import (
    BodyKind,
    BodyStatus,
    ContentKind,
    SubscriptionKind,
)
from app.database.models.subscription import Subscription
from app.ingest.operations.content import (
    BodyDraft,
    ContentItemDraft,
    ensure_content_item,
    mark_body_unavailable,
    needs_body_fetch,
    save_body,
)


def test_needs_body_fetch_pending():
    item = ContentItem(
        subscription_id=uuid.uuid4(),
        external_id="abc123",
        kind=ContentKind.VIDEO,
        title="t",
        url="https://youtube.com/watch?v=abc123",
        published_at=datetime.now(timezone.utc),
        body_status=BodyStatus.PENDING,
    )
    assert needs_body_fetch(item) is True


def test_needs_body_fetch_unavailable():
    item = ContentItem(
        subscription_id=uuid.uuid4(),
        external_id="abc123",
        kind=ContentKind.VIDEO,
        title="t",
        url="https://youtube.com/watch?v=abc123",
        published_at=datetime.now(timezone.utc),
        body_status=BodyStatus.UNAVAILABLE,
    )
    assert needs_body_fetch(item) is True


def test_needs_body_fetch_available():
    item = ContentItem(
        subscription_id=uuid.uuid4(),
        external_id="abc123",
        kind=ContentKind.VIDEO,
        title="t",
        url="https://youtube.com/watch?v=abc123",
        published_at=datetime.now(timezone.utc),
        body_status=BodyStatus.AVAILABLE,
    )
    assert needs_body_fetch(item) is False


def test_ensure_content_item_creates_new():
    session = MagicMock()
    session.scalar.return_value = None
    subscription_id = uuid.uuid4()
    draft = ContentItemDraft(
        external_id="video123",
        kind=ContentKind.VIDEO,
        title="Test video",
        url="https://youtube.com/watch?v=video123",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    item, created = ensure_content_item(session, subscription_id, draft)

    assert created is True
    assert item.external_id == "video123"
    assert item.body_status == BodyStatus.PENDING
    session.add.assert_called_once_with(item)


def test_ensure_content_item_returns_existing():
    session = MagicMock()
    existing = ContentItem(
        subscription_id=uuid.uuid4(),
        external_id="video123",
        kind=ContentKind.VIDEO,
        title="Existing",
        url="https://youtube.com/watch?v=video123",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    session.scalar.return_value = existing
    draft = ContentItemDraft(
        external_id="video123",
        kind=ContentKind.VIDEO,
        title="Test video",
        url="https://youtube.com/watch?v=video123",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    item, created = ensure_content_item(session, uuid.uuid4(), draft)

    assert created is False
    assert item is existing
    session.add.assert_not_called()


def test_save_body_sets_available_status():
    session = MagicMock()
    session.scalar.return_value = None
    item = ContentItem(
        id=uuid.uuid4(),
        subscription_id=uuid.uuid4(),
        external_id="video123",
        kind=ContentKind.VIDEO,
        title="Test",
        url="https://youtube.com/watch?v=video123",
        published_at=datetime.now(timezone.utc),
        body_status=BodyStatus.PENDING,
    )
    body = BodyDraft(
        body_kind=BodyKind.TRANSCRIPT,
        text="hello world",
        snippets=[{"text": "hello", "start": 0.0, "duration": 1.0}],
        language_code="en",
        is_generated=False,
    )

    save_body(session, item, body)

    assert item.body_status == BodyStatus.AVAILABLE
    session.add.assert_called_once()


def test_mark_body_unavailable_sets_status():
    session = MagicMock()
    session.scalar.return_value = None
    item = ContentItem(
        id=uuid.uuid4(),
        subscription_id=uuid.uuid4(),
        external_id="video123",
        kind=ContentKind.VIDEO,
        title="Test",
        url="https://youtube.com/watch?v=video123",
        published_at=datetime.now(timezone.utc),
        body_status=BodyStatus.PENDING,
    )

    mark_body_unavailable(session, item, BodyKind.TRANSCRIPT, "no captions")

    assert item.body_status == BodyStatus.UNAVAILABLE
    session.add.assert_called_once()
