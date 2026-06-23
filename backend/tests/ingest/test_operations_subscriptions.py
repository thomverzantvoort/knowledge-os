from unittest.mock import MagicMock

import pytest

from app.database.models.enums import SubscriptionKind
from app.database.models.subscription import Subscription
from app.ingest.operations.subscriptions import (
    ensure_subscription,
    set_subscription_metadata,
)


def test_ensure_subscription_creates_new():
    session = MagicMock()
    session.scalar.return_value = None

    subscription, created = ensure_subscription(
        session, SubscriptionKind.YOUTUBE_CHANNEL, "UCtest123"
    )

    assert created is True
    assert subscription.external_id == "UCtest123"
    assert subscription.kind == SubscriptionKind.YOUTUBE_CHANNEL
    session.add.assert_called_once_with(subscription)


def test_ensure_subscription_returns_existing():
    session = MagicMock()
    existing = Subscription(
        kind=SubscriptionKind.YOUTUBE_CHANNEL,
        external_id="UCtest123",
        is_active=True,
    )
    session.scalar.return_value = existing

    subscription, created = ensure_subscription(
        session, SubscriptionKind.YOUTUBE_CHANNEL, "UCtest123"
    )

    assert created is False
    assert subscription is existing
    session.add.assert_not_called()


def test_ensure_subscription_kind_mismatch_raises():
    session = MagicMock()
    existing = MagicMock()
    existing.external_id = "UCtest123"
    existing.kind = "other_kind"
    session.scalar.return_value = existing

    with pytest.raises(ValueError, match="exists with kind"):
        ensure_subscription(session, SubscriptionKind.YOUTUBE_CHANNEL, "UCtest123")


def test_set_subscription_metadata_updates_fields():
    session = MagicMock()
    subscription = Subscription(
        kind=SubscriptionKind.YOUTUBE_CHANNEL,
        external_id="UCtest123",
    )

    set_subscription_metadata(session, subscription, "Fireship", "https://youtube.com/@fireship")

    assert subscription.title == "Fireship"
    assert subscription.url == "https://youtube.com/@fireship"
