import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.config import Settings
from app.database.models.content_item import ContentItem
from app.database.models.enums import ContentKind, ProcessingStatus, UserStatus
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
    )
    monkeypatch.setattr("app.config.settings", test_settings)
    monkeypatch.setattr("app.api.auth.settings", test_settings)
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


def _item() -> ContentItem:
    return ContentItem(
        id=uuid.uuid4(),
        subscription_id=uuid.uuid4(),
        external_id="abc123xyz01",
        kind=ContentKind.VIDEO,
        title="Test video",
        url="https://youtube.com/watch?v=abc123xyz01",
        published_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        user_status=UserStatus.UNREAD,
        processing_status=ProcessingStatus.INGESTED,
    )


def test_patch_status_requires_auth(auth_settings: Settings) -> None:
    client = TestClient(app)
    item_id = uuid.uuid4()
    response = client.patch(
        f"/api/items/{item_id}/status",
        json={"status": "interested"},
    )
    assert response.status_code == 401


def test_patch_status_to_interested_schedules_deep_processing(
    auth_settings: Settings,
    auth_headers: dict[str, str],
) -> None:
    item = _item()
    db = AsyncMock()
    db.get = AsyncMock(return_value=item)
    db.scalar = AsyncMock(return_value=None)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with patch(
        "app.api.routes.items.schedule_deep_processing"
    ) as schedule_deep:
        client = TestClient(app)
        response = client.patch(
            f"/api/items/{item.id}/status",
            json={"status": "interested"},
            headers=auth_headers,
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["user_status"] == "interested"
    assert response.json()["processing_status"] == "ingested"
    schedule_deep.assert_called_once_with(item.id)


def test_patch_status_not_found(
    auth_settings: Settings,
    auth_headers: dict[str, str],
) -> None:
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    response = client.patch(
        f"/api/items/{uuid.uuid4()}/status",
        json={"status": "dismissed"},
        headers=auth_headers,
    )

    app.dependency_overrides.clear()
    assert response.status_code == 404
