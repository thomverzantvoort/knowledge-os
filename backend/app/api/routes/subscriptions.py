import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.auth import get_current_user
from app.api.deps import DbSession
from app.api.schemas import SubscriptionOut, SyncResultOut
from app.config import settings
from app.database.models.subscription import Subscription
from app.ingest.jobs.sync_subscription import SyncSubscriptionResult
from app.ingest.runner import run_sync
from app.processing.runner import run_enrichment

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _aggregate_sync_results(
    results: list[SyncSubscriptionResult],
    enrichment: dict[str, int],
) -> SyncResultOut:
    return SyncResultOut(
        subscriptions_synced=len(results),
        items_created=sum(r.items_created for r in results),
        bodies_fetched=sum(r.bodies_fetched for r in results),
        bodies_failed=sum(r.bodies_failed for r in results),
        enriched=enrichment["processed"],
        enrichment_failed=enrichment["failed"],
    )


@router.get("", response_model=list[SubscriptionOut])
async def list_subscriptions(
    db: DbSession,
    _user: Annotated[str, Depends(get_current_user)],
) -> list[SubscriptionOut]:
    rows = (
        await db.scalars(
            select(Subscription)
            .where(Subscription.is_active.is_(True))
            .order_by(Subscription.title.asc().nulls_last())
        )
    ).all()
    return [
        SubscriptionOut(id=row.id, title=row.title, url=row.url) for row in rows
    ]


@router.post("/sync", response_model=SyncResultOut)
async def sync_subscriptions(
    _user: Annotated[str, Depends(get_current_user)],
) -> SyncResultOut:
    results = await asyncio.to_thread(run_sync)
    enrichment = await asyncio.to_thread(
        run_enrichment,
        window_hours=settings.ingest_sync_window_hours,
    )
    return _aggregate_sync_results(results, enrichment)
