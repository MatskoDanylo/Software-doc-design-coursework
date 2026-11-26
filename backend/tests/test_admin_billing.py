from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import Notification, Subscription
from tests.billing_helpers import checkout, days_left, me, rows, settle
from tests.helpers import assert_error


def user_id(client: TestClient, headers: dict[str, str]) -> int:
    return client.get("/api/users/me", headers=headers).json()["id"]


def resolve(client: TestClient, admin: dict[str, str], payment_id: int, outcome: str) -> Any:
    return client.post(f"/api/admin/payments/{payment_id}/resolve", json={"outcome": outcome}, headers=admin)


def pending_payment(client: TestClient, headers: dict[str, str]) -> int:
    payment_id = checkout(client, headers)["payment_id"]
    settle(client, headers, payment_id, "pending")
    return payment_id


def test_admin_resolves_pending_payment_as_success(
    client: TestClient, buyer: dict[str, str], admin_headers: dict[str, str]
) -> None:
    payment_id = pending_payment(client, buyer)

    r = resolve(client, admin_headers, payment_id, "success")

    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["id"], body["status"], body["user_email"]) == (payment_id, "success", "user@example.com")
    assert me(client, buyer)["plan_code"] == "premium"
    assert [n.kind for n in rows(Notification)] == ["payment_pending", "subscription_activated"]


def test_admin_resolves_pending_payment_as_failed(
    client: TestClient, buyer: dict[str, str], admin_headers: dict[str, str]
) -> None:
    payment_id = pending_payment(client, buyer)

    assert resolve(client, admin_headers, payment_id, "failed").json()["status"] == "failed"
    assert me(client, buyer)["plan_code"] == "free"
    assert rows(Subscription) == []


def test_admin_can_resolve_only_pending_payments(
    client: TestClient, buyer: dict[str, str], admin_headers: dict[str, str]
) -> None:
    created = checkout(client, buyer)["payment_id"]
    succeeded = checkout(client, buyer)["payment_id"]
    settle(client, buyer, succeeded, "success")

    assert_error(resolve(client, admin_headers, created, "success"), 409, "payment_not_pending")
    assert_error(resolve(client, admin_headers, succeeded, "failed"), 409, "payment_not_pending")
    assert_error(resolve(client, admin_headers, 999_999, "success"), 404, "payment_not_found")
    assert_error(resolve(client, admin_headers, created, "pending"), 422, "validation_error")


def test_admin_resolve_works_when_mock_endpoint_is_disabled(
    client: TestClient,
    buyer: dict[str, str],
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payment_id = pending_payment(client, buyer)
    monkeypatch.setattr(settings, "payments_mock_enabled", False)

    assert resolve(client, admin_headers, payment_id, "success").json()["status"] == "success"


def test_admin_payments_filter_and_pagination(
    client: TestClient, buyer: dict[str, str], stranger: dict[str, str], admin_headers: dict[str, str]
) -> None:
    first = pending_payment(client, buyer)
    checkout(client, buyer)
    second = pending_payment(client, stranger)
    third = pending_payment(client, buyer)

    page1 = client.get("/api/admin/payments", params={"status": "pending", "page_size": 2}, headers=admin_headers)
    page2 = client.get(
        "/api/admin/payments", params={"status": "pending", "page": 2, "page_size": 2}, headers=admin_headers
    )
    everything = client.get("/api/admin/payments", headers=admin_headers).json()

    assert page1.status_code == 200, page1.text
    assert {k: v for k, v in page1.json().items() if k != "items"} == {"total": 3, "page": 1, "page_size": 2}
    assert [(p["id"], p["user_email"]) for p in page1.json()["items"]] == [
        (third, "user@example.com"),
        (second, "stranger@example.com"),
    ]
    assert [p["id"] for p in page2.json()["items"]] == [first]
    assert everything["total"] == 4
    assert_error(
        client.get("/api/admin/payments", params={"status": "refunded"}, headers=admin_headers), 422, "validation_error"
    )


def test_admin_grants_and_revokes_premium(
    client: TestClient, buyer: dict[str, str], admin_headers: dict[str, str]
) -> None:
    target = user_id(client, buyer)

    granted = client.post(
        f"/api/admin/users/{target}/subscription", json={"action": "grant", "days": 7}, headers=admin_headers
    )

    assert granted.status_code == 200, granted.text
    assert (granted.json()["plan_code"], granted.json()["cancelled"]) == ("premium", False)
    assert timedelta(days=6) < days_left(granted.json()["expires_at"]) <= timedelta(days=7)
    assert me(client, buyer) == granted.json()
    assert [n.kind for n in rows(Notification)] == ["subscription_activated"]

    revoked = client.post(f"/api/admin/users/{target}/subscription", json={"action": "revoke"}, headers=admin_headers)

    assert revoked.json() == {"plan_code": "free", "expires_at": None, "cancelled": False}
    assert me(client, buyer)["plan_code"] == "free"


def test_admin_grant_defaults_to_plan_duration(
    client: TestClient, buyer: dict[str, str], admin_headers: dict[str, str]
) -> None:
    r = client.post(
        f"/api/admin/users/{user_id(client, buyer)}/subscription", json={"action": "grant"}, headers=admin_headers
    )

    assert timedelta(days=29) < days_left(r.json()["expires_at"]) <= timedelta(days=30)


def test_admin_subscription_validation(
    client: TestClient, buyer: dict[str, str], admin_headers: dict[str, str]
) -> None:
    target = user_id(client, buyer)

    assert_error(
        client.post("/api/admin/users/999999/subscription", json={"action": "grant"}, headers=admin_headers),
        404,
        "user_not_found",
    )
    assert_error(
        client.post(f"/api/admin/users/{target}/subscription", json={"action": "upgrade"}, headers=admin_headers),
        422,
        "validation_error",
    )
    assert_error(
        client.post(
            f"/api/admin/users/{target}/subscription", json={"action": "grant", "days": 0}, headers=admin_headers
        ),
        422,
        "validation_error",
    )


def test_admin_billing_requires_admin_role(client: TestClient, buyer: dict[str, str]) -> None:
    target = user_id(client, buyer)

    assert_error(client.get("/api/admin/payments", headers=buyer), 403, "forbidden")
    assert_error(resolve(client, buyer, 1, "success"), 403, "forbidden")
    assert_error(
        client.post(f"/api/admin/users/{target}/subscription", json={"action": "grant"}, headers=buyer),
        403,
        "forbidden",
    )
    assert client.get("/api/admin/payments").status_code == 401
