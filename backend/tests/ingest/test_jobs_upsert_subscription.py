from unittest.mock import MagicMock, patch

import pytest

from app.database.models.enums import SubscriptionKind
from app.database.models.subscription import Subscription
from app.ingest.jobs.upsert_subscription import (
    UpsertSubscriptionResult,
    upsert_subscription,
    upsert_subscriptions,
)
from app.ingest.operations.subscriptions import SubscriptionInput


def test_upsert_subscription_enriches_when_metadata_missing():
    session = MagicMock()
    subscription = Subscription(
        kind=SubscriptionKind.YOUTUBE_CHANNEL,
        external_id="UCtest123",
    )

    with (
        patch(
            "app.ingest.jobs.upsert_subscription.ensure_subscription",
            return_value=(subscription, True),
        ),
        patch(
            "app.ingest.jobs.upsert_subscription._fetch_metadata",
            return_value=("Fireship", "https://youtube.com/@fireship"),
        ),
    ):
        result = upsert_subscription(
            session,
            SubscriptionInput(
                kind=SubscriptionKind.YOUTUBE_CHANNEL,
                external_id="UCtest123",
            ),
        )

    assert result.created is True
    assert result.enriched is True
    assert subscription.title == "Fireship"
    assert subscription.url == "https://youtube.com/@fireship"
    assert session.commit.call_count == 2


def test_upsert_subscription_skips_enrich_when_metadata_present():
    session = MagicMock()
    subscription = Subscription(
        kind=SubscriptionKind.YOUTUBE_CHANNEL,
        external_id="UCtest123",
        title="Fireship",
        url="https://youtube.com/@fireship",
    )

    with (
        patch(
            "app.ingest.jobs.upsert_subscription.ensure_subscription",
            return_value=(subscription, False),
        ),
        patch("app.ingest.jobs.upsert_subscription._fetch_metadata") as fetch_metadata,
    ):
        result = upsert_subscription(
            session,
            SubscriptionInput(
                kind=SubscriptionKind.YOUTUBE_CHANNEL,
                external_id="UCtest123",
            ),
        )

    fetch_metadata.assert_not_called()
    assert result.created is False
    assert result.enriched is False
    session.commit.assert_called_once()


def test_upsert_subscriptions_continues_after_failure():
    session = MagicMock()
    payloads = [
        SubscriptionInput(
            kind=SubscriptionKind.YOUTUBE_CHANNEL,
            external_id="UCbad",
        ),
        SubscriptionInput(
            kind=SubscriptionKind.YOUTUBE_CHANNEL,
            external_id="UCgood",
        ),
    ]

    def fake_upsert(sess, payload):
        if payload.external_id == "UCbad":
            raise ValueError("RSS feed parse failed")
        return UpsertSubscriptionResult(created=True, enriched=True)

    with patch(
        "app.ingest.jobs.upsert_subscription.upsert_subscription",
        side_effect=fake_upsert,
    ):
        result = upsert_subscriptions(session, payloads)

    assert result.created == 1
    assert result.failed == [("UCbad", "RSS feed parse failed")]
    session.rollback.assert_called_once()
