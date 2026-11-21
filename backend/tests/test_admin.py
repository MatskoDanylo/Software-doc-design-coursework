from fastapi.testclient import TestClient

from app.core.config import settings
from tests.helpers import assert_error, register


def test_admin_endpoint_requires_auth(client: TestClient) -> None:
    assert_error(client.get("/api/admin/users"), 401, "unauthorized")


def test_admin_endpoint_forbidden_for_regular_user(client: TestClient, user_headers: dict[str, str]) -> None:
    assert_error(client.get("/api/admin/users", headers=user_headers), 403, "forbidden")


def test_admin_lists_users(client: TestClient, admin_headers: dict[str, str]) -> None:
    register(client, "neo@example.com")

    r = client.get("/api/admin/users", headers=admin_headers)

    assert r.status_code == 200
    assert [(u["email"], u["role"]) for u in r.json()] == [(settings.admin_email, "admin"), ("neo@example.com", "user")]


def test_admin_users_pagination(client: TestClient, admin_headers: dict[str, str]) -> None:
    for name in ("a", "b", "c"):
        register(client, f"{name}@example.com")

    r = client.get("/api/admin/users", headers=admin_headers, params={"limit": 2, "offset": 1})

    assert [u["email"] for u in r.json()] == ["a@example.com", "b@example.com"]
    assert_error(client.get("/api/admin/users", headers=admin_headers, params={"limit": 0}), 422, "validation_error")
