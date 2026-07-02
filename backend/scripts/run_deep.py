import logging
from uuid import UUID

from app.processing.runner import run_deep_for_item, run_deep_pending

logger = logging.getLogger(__name__)


def _print_deep_results(counts: dict[str, int]) -> None:
    print("Deep processing complete")
    print("  processed:", counts["processed"])
    print("  skipped:", counts["skipped"])
    print("  failed:", counts["failed"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Set to a content_items.id UUID to process one item; None runs pending batch
    CONTENT_ITEM_ID: UUID | None = "73f1977c-7862-45e5-8656-f78cc0abfecf"

    if CONTENT_ITEM_ID is not None:
        run_deep_for_item(CONTENT_ITEM_ID)
        print("Deep processing finished for item", CONTENT_ITEM_ID)
    else:
        _print_deep_results(run_deep_pending())
