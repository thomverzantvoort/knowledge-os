import logging

from app.config import settings
from app.database.session import get_session
from app.ingest.jobs.sync_all import sync_all_subscriptions
from app.ingest.jobs.sync_subscription import SyncSubscriptionResult

logger = logging.getLogger(__name__)


def run_initial_ingest() -> list[SyncSubscriptionResult]:
    return _run_sync(hours=settings.ingest_initial_window_hours)


def run_sync() -> list[SyncSubscriptionResult]:
    return _run_sync(hours=settings.ingest_sync_window_hours)


def _run_sync(*, hours: int) -> list[SyncSubscriptionResult]:
    with get_session() as session:
        results = sync_all_subscriptions(session, hours=hours)
    return results
