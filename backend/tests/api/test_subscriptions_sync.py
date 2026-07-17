from unittest.mock import patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.ingest.jobs.sync_subscription import SyncSubscriptionResult
from app.main import app


@pytest.fixture
def auth_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    password_hash = bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode("utf-8")
    test_settings = Settings(
        postgres_user="test",
        postgres_password="test",
        postgres_db="test",
        auth_username="admin",
        auth_password_hash=password_hash,
        jwt_secret="test-jwt-secret-at-least-32-chars-long",
        ingest_sync_window_hours=168,
    )
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.api.auth.settings", test_settings)
    monkeypatch.setattr("app.api.routes.subscriptions.settings", test_settings)
    return test_settings


@pytest.fixture
def auth_headers(auth_settings: Settings) -> dict[str, str]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_sync_requires_auth(auth_settings: Settings) -> None:
    client = TestClient(app)
    response = client.post("/api/subscriptions/sync")
    assert response.status_code == 401


def test_sync_returns_aggregated_counts(
    auth_settings: Settings,
    auth_headers: dict[str, str],
) -> None:
    sync_results = [
        SyncSubscriptionResult(
            subscription_external_id="ch1",
            items_created=2,
            bodies_fetched=2,
            bodies_failed=0,
        ),
        SyncSubscriptionResult(
            subscription_external_id="ch2",
            items_created=1,
            bodies_fetched=0,
            bodies_failed=1,
        ),
    ]
    enrichment = {"processed": 3, "failed": 0}

    with (
        patch(
            "app.api.routes.subscriptions.run_sync",
            return_value=sync_results,
        ) as mock_sync,
        patch(
            "app.api.routes.subscriptions.run_enrichment",
            return_value=enrichment,
        ) as mock_enrich,
    ):
        client = TestClient(app)
        response = client.post(
            "/api/subscriptions/sync",
            headers=auth_headers,
        )

    assert response.status_code == 200
    assert response.json() == {
        "subscriptions_synced": 2,
        "items_created": 3,
        "bodies_fetched": 2,
        "bodies_failed": 1,
        "enriched": 3,
        "enrichment_failed": 0,
    }
    mock_sync.assert_called_once_with()
    mock_enrich.assert_called_once_with(window_hours=168)
