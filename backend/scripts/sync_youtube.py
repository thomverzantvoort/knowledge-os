import logging

from app.config import settings
from app.ingest.jobs.sync_subscription import SyncSubscriptionResult
from app.ingest.runner import run_sync
from app.processing.runner import run_enrichment

logger = logging.getLogger(__name__)


def _print_sync_results(results: list[SyncSubscriptionResult]) -> None:
    print("Sync complete")
    print("  window_hours:", settings.ingest_sync_window_hours)
    print("  subscriptions_synced:", len(results))
    for result in results:
        print()
        print(" ", result.subscription_external_id)
        print("    items_seen:", result.items_seen)
        print("    items_created:", result.items_created)
        print("    bodies_fetched:", result.bodies_fetched)
        print("    bodies_failed:", result.bodies_failed)
        print("    skipped_existing:", result.skipped_existing)


def _print_enrichment_results(counts: dict[str, int]) -> None:
    print()
    print("Enrichment complete")
    print("  window_hours:", settings.ingest_sync_window_hours)
    print("  processed:", counts["processed"])
    print("  failed:", counts["failed"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _print_sync_results(run_sync())
    _print_enrichment_results(
        run_enrichment(window_hours=settings.ingest_sync_window_hours)
    )
