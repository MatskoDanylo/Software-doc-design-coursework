from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models import Favorite
from tests.factories import make_title
from tests.helpers import PASSWORD, assert_error, bearer, login, register


@pytest.fixture
def titles() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        return {name: make_title(session, name, rating=rating).id
                for name, rating in (("Heat", 8.3), ("Ronin", 7.2), ("Alien", 8.5))}


def favorites(client: TestClient, headers: dict[str, str], **params: int) -> dict[str, Any]:
    r = client.get("/api/favorites", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def names(page: dict[str, Any]) -> list[str]:
    return [item["name"] for item in page["items"]]


def favorite_rows() -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(Favorite)) or 0


def test_add_favorite_is_idempotent(client: TestClient, user_headers: dict[str, str], titles: dict[str, int]) -> None:
    for _ in range(2):
        r = client.post(f"/api/favorites/{titles['Heat']}", headers=user_headers)
        assert r.status_code == 204, r.text

    assert favorite_rows() == 1
    page = favorites(client, user_headers)
    assert (names(page), page["total"]) == (["Heat"], 1)
    assert page["items"][0]["is_favorite"] is True
    assert set(page["items"][0]) == {
        "id", "kind", "name", "description", "year", "country", "rating", "poster_url", "genres", "is_favorite",
    }


def test_remove_favorite_is_idempotent(
    client: TestClient, user_headers: dict[str, str], titles: dict[str, int]
) -> None:
    client.post(f"/api/favorites/{titles['Heat']}", headers=user_headers)

    for _ in range(2):
        r = client.delete(f"/api/favorites/{titles['Heat']}", headers=user_headers)
        assert r.status_code == 204, r.text

    assert favorites(client, user_headers)["total"] == 0
    assert client.delete("/api/favorites/999", headers=user_headers).status_code == 204


def test_list_is_newest_first_and_paginated(
    client: TestClient, user_headers: dict[str, str], titles: dict[str, int]
) -> None:
    for name in ("Ronin", "Alien", "Heat"):
        client.post(f"/api/favorites/{titles[name]}", headers=user_headers)

    first = favorites(client, user_headers, page=1, page_size=2)
    second = favorites(client, user_headers, page=2, page_size=2)

    assert (names(first), first["total"], first["page"], first["page_size"]) == (["Heat", "Alien"], 3, 1, 2)
    assert names(second) == ["Ronin"]


def test_favorites_are_per_user(client: TestClient, user_headers: dict[str, str], titles: dict[str, int]) -> None:
    register(client, "other@example.com")
    other = bearer(login(client, "other@example.com", PASSWORD).json()["access_token"])
    client.post(f"/api/favorites/{titles['Heat']}", headers=user_headers)

    assert favorites(client, other)["total"] == 0
    assert client.get(f"/api/titles/{titles['Heat']}", headers=other).json()["is_favorite"] is False


def test_unknown_title_returns_404(client: TestClient, user_headers: dict[str, str]) -> None:
    assert_error(client.post("/api/favorites/999", headers=user_headers), 404, "title_not_found")


@pytest.mark.parametrize(("method", "path"), [("GET", "/api/favorites"), ("POST", "/api/favorites/1"),
                                              ("DELETE", "/api/favorites/1")])
def test_favorites_require_authentication(client: TestClient, method: str, path: str) -> None:
    assert_error(client.request(method, path), 401, "unauthorized")


def test_catalog_marks_favorites_for_signed_in_user(
    client: TestClient, user_headers: dict[str, str], titles: dict[str, int]
) -> None:
    client.post(f"/api/favorites/{titles['Alien']}", headers=user_headers)

    listed = client.get("/api/titles", params={"sort": "name"}, headers=user_headers).json()
    detail = client.get(f"/api/titles/{titles['Alien']}", headers=user_headers).json()
    other = client.get(f"/api/titles/{titles['Heat']}", headers=user_headers).json()

    assert {i["name"]: i["is_favorite"] for i in listed["items"]} == {"Alien": True, "Heat": False, "Ronin": False}
    assert (detail["is_favorite"], other["is_favorite"]) == (True, False)
    assert "seasons" in detail


def test_guest_sees_is_favorite_false(client: TestClient, user_headers: dict[str, str], titles: dict[str, int]) -> None:
    client.post(f"/api/favorites/{titles['Alien']}", headers=user_headers)

    listed = client.get("/api/titles").json()

    assert all(item["is_favorite"] is False for item in listed["items"])
    assert client.get(f"/api/titles/{titles['Alien']}").json()["is_favorite"] is False


def test_catalog_rejects_invalid_token(client: TestClient, titles: dict[str, int]) -> None:
    assert_error(client.get("/api/titles", headers=bearer("garbage")), 401, "invalid_token")


def test_deleting_title_removes_it_from_favorites(
    client: TestClient, user_headers: dict[str, str], admin_headers: dict[str, str], titles: dict[str, int]
) -> None:
    client.post(f"/api/favorites/{titles['Heat']}", headers=user_headers)

    assert client.delete(f"/api/admin/titles/{titles['Heat']}", headers=admin_headers).status_code == 204

    assert favorites(client, user_headers)["total"] == 0
