import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApiException

from app.database.models.enums import BodyKind, ContentKind, SubscriptionKind
from app.database.models.subscription import Subscription
from app.ingest.adapters.youtube import Transcript, VideoData, YouTubeScraper
from app.ingest.operations.content import (
    BodyDraft,
    ContentItemDraft,
    ensure_content_item,
    mark_body_unavailable,
    needs_body_fetch,
    save_body,
)
from app.ingest.operations.subscriptions import set_last_synced_at

logger = logging.getLogger(__name__)


@dataclass
class SyncSubscriptionResult:
    subscription_external_id: str
    items_seen: int = 0
    items_created: int = 0
    bodies_fetched: int = 0
    bodies_failed: int = 0
    skipped_existing: int = 0


def _video_to_draft(video: VideoData) -> ContentItemDraft:
    return ContentItemDraft(
        external_id=video.video_id,
        kind=ContentKind.VIDEO,
        title=video.title,
        description=video.description or None,
        url=video.url,
        thumbnail_url=video.thumbnail_url,
        author=video.channel_title or None,
        published_at=video.published_at,
    )


def _transcript_to_body(transcript: Transcript) -> BodyDraft:
    return BodyDraft(
        body_kind=BodyKind.TRANSCRIPT,
        text=transcript.text,
        snippets=[snippet.model_dump() for snippet in transcript.snippets],
        language_code=transcript.language_code,
        is_generated=transcript.is_generated,
    )


def sync_youtube_subscription(
    session: Session,
    subscription: Subscription,
    *,
    hours: int,
    scraper: YouTubeScraper,
) -> SyncSubscriptionResult:
    result = SyncSubscriptionResult(subscription_external_id=subscription.external_id)
    videos = scraper.get_channel_videos(subscription.external_id, hours=hours)
    result.items_seen = len(videos)

    for video in videos:
        draft = _video_to_draft(video)
        item, created = ensure_content_item(session, subscription.id, draft)
        if created:
            result.items_created += 1

        if not created and not needs_body_fetch(item):
            result.skipped_existing += 1
            continue

        try:
            transcript = scraper.get_transcript(video.video_id)
            save_body(session, item, _transcript_to_body(transcript))
            result.bodies_fetched += 1
        except YouTubeTranscriptApiException as error:
            mark_body_unavailable(
                session, item, BodyKind.TRANSCRIPT, str(error)
            )
            result.bodies_failed += 1
            logger.warning(
                "Transcript unavailable for %s: %s",
                video.video_id,
                error,
            )

    set_last_synced_at(session, subscription, datetime.now(timezone.utc))
    session.commit()
    return result


def sync_subscription(
    session: Session,
    subscription: Subscription,
    *,
    hours: int,
    scraper: YouTubeScraper,
) -> SyncSubscriptionResult:
    if subscription.kind == SubscriptionKind.YOUTUBE_CHANNEL:
        return sync_youtube_subscription(
            session, subscription, hours=hours, scraper=scraper
        )
    raise ValueError(f"Unsupported subscription kind: {subscription.kind}")
