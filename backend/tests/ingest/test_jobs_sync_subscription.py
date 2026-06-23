import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from youtube_transcript_api import YouTubeTranscriptApiException

from app.database.models.content_item import ContentItem
from app.database.models.enums import BodyStatus, ContentKind, SubscriptionKind
from app.database.models.subscription import Subscription
from app.ingest.adapters.youtube import Transcript, TranscriptSnippet, VideoData
from app.ingest.jobs.sync_subscription import sync_youtube_subscription


def _video() -> VideoData:
    return VideoData(
        video_id="abc123xyz01",
        title="Test video",
        description="desc",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        url="https://youtube.com/watch?v=abc123xyz01",
        channel_title="Test Channel",
        thumbnail_url="https://i.ytimg.com/vi/abc123xyz01/hqdefault.jpg",
    )


def _subscription() -> Subscription:
    return Subscription(
        id=uuid.uuid4(),
        kind=SubscriptionKind.YOUTUBE_CHANNEL,
        external_id="UCtest123",
    )


def test_sync_skips_transcript_when_body_available():
    session = MagicMock()
    subscription = _subscription()
    video = _video()
    scraper = MagicMock()
    scraper.get_channel_videos.return_value = [video]
    existing_item = ContentItem(
        id=uuid.uuid4(),
        subscription_id=subscription.id,
        external_id=video.video_id,
        kind=ContentKind.VIDEO,
        title=video.title,
        url=video.url,
        published_at=video.published_at,
        body_status=BodyStatus.AVAILABLE,
    )

    with patch(
        "app.ingest.jobs.sync_subscription.ensure_content_item",
        return_value=(existing_item, False),
    ):
        result = sync_youtube_subscription(
            session, subscription, hours=168, scraper=scraper
        )

    scraper.get_transcript.assert_not_called()
    assert result.skipped_existing == 1
    assert result.bodies_fetched == 0


def test_sync_fetches_transcript_for_new_item():
    session = MagicMock()
    subscription = _subscription()
    video = _video()
    scraper = MagicMock()
    scraper.get_channel_videos.return_value = [video]
    scraper.get_transcript.return_value = Transcript(
        text="hello",
        language="English",
        language_code="en",
        is_generated=False,
        snippets=[TranscriptSnippet(text="hello", start=0.0, duration=1.0)],
    )
    new_item = ContentItem(
        id=uuid.uuid4(),
        subscription_id=subscription.id,
        external_id=video.video_id,
        kind=ContentKind.VIDEO,
        title=video.title,
        url=video.url,
        published_at=video.published_at,
        body_status=BodyStatus.PENDING,
    )

    with (
        patch(
            "app.ingest.jobs.sync_subscription.ensure_content_item",
            return_value=(new_item, True),
        ),
        patch("app.ingest.jobs.sync_subscription.save_body") as save_body,
    ):
        result = sync_youtube_subscription(
            session, subscription, hours=168, scraper=scraper
        )

    scraper.get_transcript.assert_called_once_with(video.video_id)
    save_body.assert_called_once()
    assert result.items_created == 1
    assert result.bodies_fetched == 1
    session.commit.assert_called_once()


def test_sync_retries_transcript_when_unavailable():
    session = MagicMock()
    subscription = _subscription()
    video = _video()
    scraper = MagicMock()
    scraper.get_channel_videos.return_value = [video]
    scraper.get_transcript.side_effect = YouTubeTranscriptApiException("video", [], [])
    item = ContentItem(
        id=uuid.uuid4(),
        subscription_id=subscription.id,
        external_id=video.video_id,
        kind=ContentKind.VIDEO,
        title=video.title,
        url=video.url,
        published_at=video.published_at,
        body_status=BodyStatus.UNAVAILABLE,
    )

    with (
        patch(
            "app.ingest.jobs.sync_subscription.ensure_content_item",
            return_value=(item, False),
        ),
        patch("app.ingest.jobs.sync_subscription.mark_body_unavailable") as mark_unavailable,
    ):
        result = sync_youtube_subscription(
            session, subscription, hours=168, scraper=scraper
        )

    scraper.get_transcript.assert_called_once()
    mark_unavailable.assert_called_once()
    assert result.bodies_failed == 1
