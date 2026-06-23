from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.enums import SubscriptionKind
from app.database.models.subscription import Subscription


class SubscriptionInput(BaseModel):
    kind: SubscriptionKind
    external_id: str = Field(min_length=1, max_length=64)
    is_active: bool = True


def list_active_subscriptions(session: Session) -> list[Subscription]:
    return list(
        session.scalars(
            select(Subscription)
            .where(Subscription.is_active.is_(True))
            .order_by(Subscription.created_at)
        )
    )


def ensure_subscription(
    session: Session,
    kind: SubscriptionKind,
    external_id: str,
    is_active: bool = True,
) -> tuple[Subscription, bool]:
    subscription = session.scalar(
        select(Subscription).where(Subscription.external_id == external_id)
    )
    if subscription is None:
        subscription = Subscription(
            kind=kind, external_id=external_id, is_active=is_active
        )
        session.add(subscription)
        return subscription, True

    if subscription.kind != kind:
        raise ValueError(
            f"Subscription {external_id} exists with kind {subscription.kind}, got {kind}"
        )

    subscription.is_active = is_active
    return subscription, False


def set_subscription_metadata(
    session: Session,
    subscription: Subscription,
    title: str | None,
    url: str | None,
) -> None:
    if title is not None:
        subscription.title = title
    if url is not None:
        subscription.url = url


def set_last_synced_at(
    session: Session,
    subscription: Subscription,
    synced_at: datetime,
) -> None:
    subscription.last_synced_at = synced_at
