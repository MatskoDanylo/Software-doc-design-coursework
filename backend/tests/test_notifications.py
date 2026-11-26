from typing import Any

from fastapi.testclient import TestClient

from tests.billing_helpers import checkout, settle
from tests.helpers import assert_error


def inbox(client: TestClient, headers: dict[str, str], **params: Any) -> dict[str, Any]:
    r = client.get("/api/notifications", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def pending_then_failed(client: TestClient, headers: dict[str, str]) -> None:
    payment_id = checkout(client, headers)["payment_id"]
    settle(client, headers, payment_id, "pending")
    settle(client, headers, payment_id, "failed")


def test_inbox_lists_payment_notifications_newest_first(client: TestClient, buyer: dict[str, str]) -> None:
    pending_then_failed(client, buyer)

    body = inbox(client, buyer)

    assert body["unread"] == 2
    assert [(n["kind"], n["read"]) for n in body["items"]] == [("payment_failed", False), ("payment_pending", False)]
    assert body["items"][0]["message"] == "Оплату 99.00 грн за Преміум відхилено. Спробуйте ще раз."
    assert set(body["items"][0]) == {"id", "kind", "message", "read", "created_at"}


def test_inbox_limit_and_unread_filter(client: TestClient, buyer: dict[str, str]) -> None:
    pending_then_failed(client, buyer)
    newest = inbox(client, buyer, limit=1)

    assert [n["kind"] for n in newest["items"]] == ["payment_failed"]
    assert newest["unread"] == 2

    r = client.post(f"/api/notifications/{newest['items'][0]['id']}/read", headers=buyer)
    assert r.status_code == 200, r.text
    assert r.json()["read"] is True

    unread = inbox(client, buyer, unread_only=True)
    assert [n["kind"] for n in unread["items"]] == ["payment_pending"]
    assert unread["unread"] == 1


def test_mark_read_is_idempotent(client: TestClient, buyer: dict[str, str]) -> None:
    pending_then_failed(client, buyer)
    notification_id = inbox(client, buyer)["items"][0]["id"]

    for _ in range(2):
        assert client.post(f"/api/notifications/{notification_id}/read", headers=buyer).json()["read"] is True
    assert inbox(client, buyer)["unread"] == 1


def test_read_all_marks_only_own_notifications(
    client: TestClient, buyer: dict[str, str], stranger: dict[str, str]
) -> None:
    pending_then_failed(client, buyer)
    pending_then_failed(client, stranger)

    r = client.post("/api/notifications/read-all", headers=buyer)

    assert r.status_code == 200
    assert r.json() == {"updated": 2}
    assert inbox(client, buyer)["unread"] == 0
    assert inbox(client, stranger)["unread"] == 2
    assert client.post("/api/notifications/read-all", headers=buyer).json() == {"updated": 0}


def test_foreign_notification_is_not_found(client: TestClient, buyer: dict[str, str], stranger: dict[str, str]) -> None:
    pending_then_failed(client, buyer)
    notification_id = inbox(client, buyer)["items"][0]["id"]

    assert_error(
        client.post(f"/api/notifications/{notification_id}/read", headers=stranger), 404, "notification_not_found"
    )
    assert inbox(client, buyer)["unread"] == 2


def test_notifications_require_auth_and_validate_limit(client: TestClient, buyer: dict[str, str]) -> None:
    assert client.get("/api/notifications").status_code == 401
    assert client.post("/api/notifications/read-all").status_code == 401
    assert_error(client.get("/api/notifications", params={"limit": 0}, headers=buyer), 422, "validation_error")
