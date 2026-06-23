import logging

from app.config import settings
from app.processing.runner import run_enrichment

logger = logging.getLogger(__name__)


def _print_enrichment_results(counts: dict[str, int]) -> None:
    print("Enrichment complete")
    print("  window_hours:", settings.enrichment_window_hours)
    print("  processed:", counts["processed"])
    print("  failed:", counts["failed"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _print_enrichment_results(run_enrichment())
