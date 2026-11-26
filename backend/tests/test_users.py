import pytest
from fastapi.testclient import TestClient

from tests.helpers import assert_error, bearer


@pytest.mark.parametrize("headers", [{}, bearer("garbage"), {"Authorization": "Basic abc"}])
def test_me_requires_valid_access_token(client: TestClient, headers: dict[str, str]) -> None:
    r = client.get("/api/users/me", headers=headers)

    assert r.status_code == 401
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_me_returns_current_user(client: TestClient, user_headers: dict[str, str]) -> None:
    r = client.get("/api/users/me", headers=user_headers)

    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"
    assert r.json()["profile"]["display_name"] == "user"


def test_patch_me_updates_and_persists_profile(client: TestClient, user_headers: dict[str, str]) -> None:
    payload = {"display_name": " Neo ", "avatar_url": "https://img.example.com/neo.png", "country": "Ukraine"}

    r = client.patch("/api/users/me", headers=user_headers, json=payload)

    expected = {"display_name": "Neo", "avatar_url": "https://img.example.com/neo.png", "country": "Ukraine"}
    assert r.status_code == 200
    assert r.json()["profile"] == expected
    assert client.get("/api/users/me", headers=user_headers).json()["profile"] == expected


def test_patch_me_is_partial(client: TestClient, user_headers: dict[str, str]) -> None:
    client.patch("/api/users/me", headers=user_headers, json={"country": "Ukraine"})

    r = client.patch("/api/users/me", headers=user_headers, json={"display_name": "Neo"})

    assert r.json()["profile"] == {"display_name": "Neo", "avatar_url": None, "country": "Ukraine"}


def test_patch_me_can_clear_optional_fields(client: TestClient, user_headers: dict[str, str]) -> None:
    client.patch("/api/users/me", headers=user_headers, json={"country": "Ukraine"})

    r = client.patch("/api/users/me", headers=user_headers, json={"country": None})

    assert r.json()["profile"]["country"] is None


@pytest.mark.parametrize(
    "payload",
    [{"display_name": None}, {"display_name": ""}, {"avatar_url": "not-a-url"}, {"country": "x" * 101}],
)
def test_patch_me_validates_input(client: TestClient, user_headers: dict[str, str], payload: dict) -> None:
    assert_error(client.patch("/api/users/me", headers=user_headers, json=payload), 422, "validation_error")


def test_patch_me_requires_auth(client: TestClient) -> None:
    assert_error(client.patch("/api/users/me", json={"country": "Ukraine"}), 401, "unauthorized")
