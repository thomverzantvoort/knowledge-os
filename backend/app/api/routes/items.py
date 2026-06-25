from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.api.auth import get_current_user
from app.api.deps import DbSession
from app.api.schemas import ContentItemOut, EnrichmentOut, PaginatedItemsOut
from app.database.models.content_item import ContentItem
from app.database.models.enums import UserStatus

router = APIRouter(prefix="/items", tags=["items"])

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


def _enrichment_from_row(data: dict | None) -> EnrichmentOut | None:
    if not data:
        return None
    required = ("blurb", "content_type", "input_kind", "enriched_at")
    if not all(key in data for key in required):
        return None
    return EnrichmentOut(
        blurb=data["blurb"],
        tags=data.get("tags", []),
        content_type=data["content_type"],
        domain_matches=data.get("domain_matches", []),
        relevance_score=float(data.get("relevance_score", 0)),
        input_kind=data["input_kind"],
        enriched_at=data["enriched_at"],
    )


def _item_to_out(item: ContentItem) -> ContentItemOut:
    return ContentItemOut(
        id=item.id,
        subscription_id=item.subscription_id,
        title=item.title,
        description=item.description,
        url=item.url,
        thumbnail_url=item.thumbnail_url,
        author=item.author,
        published_at=item.published_at,
        kind=item.kind,
        user_status=item.user_status,
        enrichment=_enrichment_from_row(item.enrichment),
    )


@router.get("", response_model=PaginatedItemsOut)
async def list_items(
    db: DbSession,
    _user: Annotated[str, Depends(get_current_user)],
    sort: Literal["chronological"] = "chronological",
    status: Literal["all", "unread", "interested", "dismissed"] = "all",
    subscription_id: UUID | None = None,
    window_hours: int | None = Query(default=168, ge=1),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    all_time: bool = Query(default=False, description="Ignore window_hours filter"),
) -> PaginatedItemsOut:
    query = select(ContentItem)
    count_query = select(func.count()).select_from(ContentItem)

    if status != "all":
        user_status = UserStatus(status)
        query = query.where(ContentItem.user_status == user_status)
        count_query = count_query.where(ContentItem.user_status == user_status)

    if subscription_id is not None:
        query = query.where(ContentItem.subscription_id == subscription_id)
        count_query = count_query.where(
            ContentItem.subscription_id == subscription_id
        )

    if not all_time and window_hours is not None:
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        query = query.where(ContentItem.published_at >= cutoff)
        count_query = count_query.where(ContentItem.published_at >= cutoff)

    if sort == "chronological":
        query = query.order_by(ContentItem.published_at.desc())

    total = (await db.scalar(count_query)) or 0
    rows = (
        await db.scalars(query.limit(limit).offset(offset))
    ).all()

    return PaginatedItemsOut(
        items=[_item_to_out(item) for item in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
