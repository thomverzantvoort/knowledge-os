from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.auth import get_current_user
from app.api.deps import DbSession
from app.api.schemas import SubscriptionOut
from app.database.models.subscription import Subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


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
