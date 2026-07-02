from uuid import UUID

from app.agents.factory import get_agent
from app.config import settings
from app.database.session import get_session
from app.processing.jobs.deep_process_item import (
    process_deep_item,
    process_pending_deep_items,
)
from app.processing.jobs.enrich_items import enrich_pending_items


def run_enrichment(*, window_hours: int | None = None) -> dict[str, int]:
    get_agent()
    hours = (
        window_hours
        if window_hours is not None
        else settings.enrichment_window_hours
    )
    with get_session() as session:
        return enrich_pending_items(session, window_hours=hours)


def run_deep_for_item(item_id: UUID) -> None:
    get_agent()
    with get_session() as session:
        process_deep_item(session, item_id)


def run_deep_pending() -> dict[str, int]:
    get_agent()
    with get_session() as session:
        return process_pending_deep_items(session)
