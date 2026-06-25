import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient

from app.api.auth import ALGORITHM, authenticate_user, create_access_token
from app.config import Settings
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


def test_authenticate_user_valid(auth_settings: Settings) -> None:
    assert authenticate_user("admin", "secret") is True


def test_authenticate_user_invalid_password(auth_settings: Settings) -> None:
    assert authenticate_user("admin", "wrong") is False


def test_authenticate_user_invalid_username(auth_settings: Settings) -> None:
    assert authenticate_user("other", "secret") is False


def test_create_and_decode_access_token(auth_settings: Settings) -> None:
    token = create_access_token("admin")
    payload = jwt.decode(token, auth_settings.jwt_secret, algorithms=[ALGORITHM])
    assert payload["sub"] == "admin"


def test_items_requires_auth(auth_settings: Settings) -> None:
    client = TestClient(app)
    response = client.get("/api/items")
    assert response.status_code == 401


def test_login_and_list_items_unauthorized_without_token(
    auth_settings: Settings,
) -> None:
    client = TestClient(app)
    bad_login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert bad_login.status_code == 401


def test_login_returns_token(auth_settings: Settings) -> None:
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"
