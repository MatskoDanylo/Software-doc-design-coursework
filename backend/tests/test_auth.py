import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import TokenType, create_token
from app.models import User
from tests.helpers import PASSWORD, assert_error, bearer, login, register


def test_register_creates_user_with_profile(client: TestClient) -> None:
    r = register(client, "  New.User@Example.COM ", display_name="Neo")

    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new.user@example.com"
    assert body["role"] == "user"
    assert body["profile"] == {"display_name": "Neo", "avatar_url": None, "country": None}
    assert "password" not in r.text and "password_hash" not in body


def test_register_defaults_display_name_to_email_local_part(client: TestClient) -> None:
    assert register(client, "trinity@example.com").json()["profile"]["display_name"] == "trinity"


@pytest.mark.parametrize("duplicate", ["taken@example.com", "TAKEN@example.com"])
def test_register_rejects_taken_email(client: TestClient, duplicate: str) -> None:
    register(client, "taken@example.com")

    assert_error(register(client, duplicate), 409, "email_taken")


@pytest.mark.parametrize(
    ("email", "password", "field"),
    [
        ("not-an-email", PASSWORD, "email"),
        ("short@example.com", "1234567", "password"),
        ("long@example.com", "ї" * 37, "password"),
    ],
)
def test_register_validates_input(client: TestClient, email: str, password: str, field: str) -> None:
    r = register(client, email, password)

    assert_error(r, 422, "validation_error")
    assert [d["loc"] for d in r.json()["error"]["details"]] == [["body", field]]


def test_login_returns_token_pair(client: TestClient) -> None:
    register(client, "neo@example.com")

    r = login(client, "NEO@example.com")

    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


@pytest.mark.parametrize(
    ("email", "password"), [("neo@example.com", "wrong-password"), ("ghost@example.com", PASSWORD)]
)
def test_login_rejects_invalid_credentials(client: TestClient, email: str, password: str) -> None:
    register(client, "neo@example.com")

    r = login(client, email, password)

    assert_error(r, 401, "invalid_credentials")
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_refresh_issues_working_tokens(client: TestClient) -> None:
    register(client, "neo@example.com")
    tokens = login(client, "neo@example.com").json()

    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert r.status_code == 200
    new = r.json()
    assert new["access_token"] != tokens["access_token"]
    assert client.get("/api/users/me", headers=bearer(new["access_token"])).status_code == 200


def test_refresh_rejects_access_token(client: TestClient) -> None:
    register(client, "neo@example.com")
    access = login(client, "neo@example.com").json()["access_token"]

    assert_error(client.post("/api/auth/refresh", json={"refresh_token": access}), 401, "invalid_token")


def test_refresh_rejects_garbage(client: TestClient) -> None:
    assert_error(client.post("/api/auth/refresh", json={"refresh_token": "garbage"}), 401, "invalid_token")


def test_expired_access_token_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = register(client, "neo@example.com").json()["id"]
    monkeypatch.setattr(settings, "access_token_minutes", -1)

    expired = create_token(user_id, TokenType.ACCESS)

    assert_error(client.get("/api/users/me", headers=bearer(expired)), 401, "invalid_token")


def test_token_of_deleted_user_is_rejected(client: TestClient) -> None:
    register(client, "neo@example.com")
    tokens = login(client, "neo@example.com").json()
    with SessionLocal() as session, session.begin():
        session.execute(delete(User).where(User.email == "neo@example.com"))

    assert_error(client.get("/api/users/me", headers=bearer(tokens["access_token"])), 401, "invalid_token")
    assert_error(
        client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}), 401, "invalid_token"
    )
