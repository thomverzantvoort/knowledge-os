import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models.enums import SubscriptionKind
from app.ingest.adapters.youtube import YouTubeScraper
from app.ingest.jobs.sync_subscription import SyncSubscriptionResult, sync_subscription
from app.ingest.operations.subscriptions import list_active_subscriptions

logger = logging.getLogger(__name__)


def build_youtube_scraper() -> YouTubeScraper:
    return YouTubeScraper(
        transcript_languages=settings.transcript_languages,
        exclude_shorts=settings.exclude_shorts,
    )


def sync_all_subscriptions(
    session: Session,
    *,
    hours: int,
    subscription_external_id: str | None = None,
) -> list[SyncSubscriptionResult]:
    filter_id = subscription_external_id or settings.ingest_subscription_id
    subscriptions = list_active_subscriptions(session)

    if filter_id is not None:
        subscriptions = [
            sub for sub in subscriptions if sub.external_id == filter_id
        ]

    scraper = build_youtube_scraper()
    results: list[SyncSubscriptionResult] = []

    for subscription in subscriptions:
        if subscription.kind != SubscriptionKind.YOUTUBE_CHANNEL:
            logger.warning(
                "Skipping subscription %s: unsupported kind %s",
                subscription.external_id,
                subscription.kind,
            )
            continue

        try:
            result = sync_subscription(
                session, subscription, hours=hours, scraper=scraper
            )
            results.append(result)
        except Exception as error:
            session.rollback()
            logger.exception(
                "Sync failed for subscription %s: %s",
                subscription.external_id,
                error,
            )

    return results
