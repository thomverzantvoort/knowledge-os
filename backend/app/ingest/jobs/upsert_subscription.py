import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.database.models.enums import SubscriptionKind
from app.ingest.adapters.youtube import get_channel_metadata
from app.ingest.operations.subscriptions import (
    SubscriptionInput,
    ensure_subscription,
    set_subscription_metadata,
)

logger = logging.getLogger(__name__)


@dataclass
class UpsertSubscriptionResult:
    created: bool
    enriched: bool = False


@dataclass
class UpsertSubscriptionsResult:
    created: int = 0
    existing: int = 0
    enriched: int = 0
    failed: list[tuple[str, str]] = field(default_factory=list)


def _fetch_metadata(
    kind: SubscriptionKind, external_id: str
) -> tuple[str | None, str | None]:
    if kind == SubscriptionKind.YOUTUBE_CHANNEL:
        return get_channel_metadata(external_id)
    raise ValueError(f"Unsupported subscription kind: {kind}")


def upsert_subscription(
    session: Session, payload: SubscriptionInput
) -> UpsertSubscriptionResult:
    subscription, was_created = ensure_subscription(
        session,
        payload.kind,
        payload.external_id,
        is_active=payload.is_active,
    )
    session.commit()

    enriched = False
    if not subscription.title or not subscription.url:
        try:
            title, url = _fetch_metadata(payload.kind, payload.external_id)
            set_subscription_metadata(session, subscription, title, url)
            session.commit()
            enriched = True
            logger.info(
                "Subscription metadata for %s: title=%s url=%s",
                subscription.external_id,
                subscription.title,
                subscription.url,
            )
        except Exception as error:
            session.rollback()
            raise error

    return UpsertSubscriptionResult(created=was_created, enriched=enriched)


def upsert_subscriptions(
    session: Session, payloads: list[SubscriptionInput]
) -> UpsertSubscriptionsResult:
    result = UpsertSubscriptionsResult()

    for payload in payloads:
        try:
            item_result = upsert_subscription(session, payload)
            if item_result.created:
                result.created += 1
            else:
                result.existing += 1
            if item_result.enriched:
                result.enriched += 1
        except Exception as error:
            session.rollback()
            result.failed.append((payload.external_id, str(error)))
            logger.warning(
                "Failed to upsert subscription %s: %s",
                payload.external_id,
                error,
            )

    return result
