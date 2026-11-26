from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_mock_gateway
from app.core.config import settings
from app.core.events import DomainEvent
from app.main import app
from app.models import Notification, Payment, Subscription, SubscriptionStatus
from app.patterns.payment_gateway import MockGatewayAdapter, MockPaymentProvider
from app.services.notification_service import NotificationService
from tests.billing_helpers import (
    checkout,
    days_left,
    me,
    mock_result,
    notification_kinds,
    payment,
    rows,
    settle,
)
from tests.helpers import assert_error
from tests.test_playback_proxy import catalog, preroll  # noqa: F401

PREMIUM_PLAN = {
    "code": "premium",
    "name": "Преміум",
    "price": "99.00",
    "currency": "UAH",
    "duration_days": 30,
    "ads_enabled": False,
    "max_height": 1080,
    "description": "99.00 грн за 30 днів. Без реклами, якість до 1080p.",
    "purchasable": True,
}


def test_plans_are_public_and_described_by_policies(client: TestClient, seeded: None) -> None:
    r = client.get("/api/plans")

    assert r.status_code == 200
    free, premium = r.json()
    assert premium == PREMIUM_PLAN
    assert (free["code"], free["price"], free["purchasable"], free["ads_enabled"]) == ("free", "0.00", False, True)


def test_checkout_creates_payment_with_policy_price(client: TestClient, buyer: dict[str, str]) -> None:
    body = checkout(client, buyer)

    assert body == {
        "payment_id": body["payment_id"],
        "amount": "99.00",
        "currency": "UAH",
        "status": "created",
        "plan": PREMIUM_PLAN,
    }
    row = payment(body["payment_id"])
    assert (row.status, row.provider, row.paid_at) == ("created", "mock", None)
    assert row.external_id is not None and row.external_id.startswith("inv_")


def test_checkout_validation(client: TestClient, buyer: dict[str, str]) -> None:
    assert_error(
        client.post("/api/billing/checkout", json={"plan_code": "free"}, headers=buyer), 422, "plan_not_purchasable"
    )
    assert_error(client.post("/api/billing/checkout", json={"plan_code": "gold"}, headers=buyer), 404, "plan_not_found")
    assert client.post("/api/billing/checkout", json={"plan_code": "premium"}).status_code == 401
    assert rows(Payment) == []


def test_success_activates_premium_and_notifies(client: TestClient, buyer: dict[str, str]) -> None:
    payment_id = checkout(client, buyer)["payment_id"]

    body = settle(client, buyer, payment_id, "success")

    assert (body["status"], body["plan_code"], body["amount"]) == ("success", "premium", "99.00")
    assert body["paid_at"] is not None
    subscription = me(client, buyer)
    assert (subscription["plan_code"], subscription["cancelled"]) == ("premium", False)
    assert timedelta(days=29) < days_left(subscription["expires_at"]) <= timedelta(days=30)
    assert notification_kinds() == ["subscription_activated"]


def test_success_unlocks_1080p_without_ads(
    client: TestClient,
    buyer: dict[str, str],
    catalog: dict[str, int],  # noqa: F811
    preroll: None,  # noqa: F811
) -> None:
    before = client.get(f"/api/titles/{catalog['movie']}/playback", headers=buyer).json()
    assert (before["plan"], before["allowed_heights"], before["ads"]["enabled"]) == ("free", [360, 720], True)

    settle(client, buyer, checkout(client, buyer)["payment_id"], "success")

    after = client.get(f"/api/titles/{catalog['movie']}/playback", headers=buyer).json()
    assert (after["plan"], after["allowed_heights"]) == ("premium", [360, 720, 1080])
    assert after["ads"] == {"enabled": False, "preroll_url": None}


def test_pending_then_success(client: TestClient, buyer: dict[str, str]) -> None:
    payment_id = checkout(client, buyer)["payment_id"]

    assert settle(client, buyer, payment_id, "pending")["status"] == "pending"
    assert me(client, buyer)["plan_code"] == "free"
    assert notification_kinds() == ["payment_pending"]

    assert settle(client, buyer, payment_id, "pending")["status"] == "pending"
    assert notification_kinds() == ["payment_pending"]

    assert settle(client, buyer, payment_id, "success")["status"] == "success"
    assert me(client, buyer)["plan_code"] == "premium"
    assert notification_kinds() == ["payment_pending", "subscription_activated"]


def test_pending_then_failed(client: TestClient, buyer: dict[str, str]) -> None:
    payment_id = checkout(client, buyer)["payment_id"]
    settle(client, buyer, payment_id, "pending")

    body = settle(client, buyer, payment_id, "failed")

    assert (body["status"], body["paid_at"]) == ("failed", None)
    assert me(client, buyer)["plan_code"] == "free"
    assert rows(Subscription) == []
    assert notification_kinds() == ["payment_pending", "payment_failed"]


@pytest.mark.parametrize("retry", ["success", "pending", "failed"])
def test_failed_payment_is_final(client: TestClient, buyer: dict[str, str], retry: str) -> None:
    payment_id = checkout(client, buyer)["payment_id"]
    assert settle(client, buyer, payment_id, "failed")["status"] == "failed"

    assert_error(mock_result(client, buyer, payment_id, retry), 409, "payment_finalized")
    assert payment(payment_id).status == "failed"
    assert notification_kinds() == ["payment_failed"]


@pytest.mark.parametrize("retry", ["pending", "failed"])
def test_successful_payment_cannot_be_changed(client: TestClient, buyer: dict[str, str], retry: str) -> None:
    payment_id = checkout(client, buyer)["payment_id"]
    settle(client, buyer, payment_id, "success")

    assert_error(mock_result(client, buyer, payment_id, retry), 409, "payment_finalized")


def test_repeated_success_is_idempotent(client: TestClient, buyer: dict[str, str]) -> None:
    payment_id = checkout(client, buyer)["payment_id"]
    first = settle(client, buyer, payment_id, "success")
    expires = me(client, buyer)["expires_at"]

    second = settle(client, buyer, payment_id, "success")

    assert second == first
    assert me(client, buyer)["expires_at"] == expires
    assert len(rows(Subscription)) == 1
    assert notification_kinds() == ["subscription_activated"]


def test_foreign_or_missing_payment_is_not_found(
    client: TestClient, buyer: dict[str, str], stranger: dict[str, str]
) -> None:
    payment_id = checkout(client, buyer)["payment_id"]

    assert_error(mock_result(client, stranger, payment_id, "success"), 404, "payment_not_found")
    assert_error(mock_result(client, buyer, 999_999, "success"), 404, "payment_not_found")
    assert payment(payment_id).status == "created"


def test_invalid_outcome_is_rejected(client: TestClient, buyer: dict[str, str]) -> None:
    payment_id = checkout(client, buyer)["payment_id"]

    assert_error(mock_result(client, buyer, payment_id, "refunded"), 422, "validation_error")


def test_second_purchase_extends_active_subscription(client: TestClient, buyer: dict[str, str]) -> None:
    settle(client, buyer, checkout(client, buyer)["payment_id"], "success")
    first_expiry = datetime.fromisoformat(me(client, buyer)["expires_at"])

    settle(client, buyer, checkout(client, buyer)["payment_id"], "success")

    assert datetime.fromisoformat(me(client, buyer)["expires_at"]) == first_expiry + timedelta(days=30)
    [subscription] = rows(Subscription)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert notification_kinds() == ["subscription_activated", "subscription_activated"]


def test_payment_history_lists_own_payments_newest_first(
    client: TestClient, buyer: dict[str, str], stranger: dict[str, str]
) -> None:
    first = checkout(client, buyer)["payment_id"]
    settle(client, buyer, first, "failed")
    second = checkout(client, buyer)["payment_id"]
    checkout(client, stranger)

    r = client.get("/api/billing/payments", headers=buyer)

    assert r.status_code == 200
    assert [(p["id"], p["status"]) for p in r.json()] == [(second, "created"), (first, "failed")]
    assert client.get("/api/billing/payments").status_code == 401


def test_pending_payment_survives_gateway_restart(client: TestClient, buyer: dict[str, str]) -> None:
    payment_id = checkout(client, buyer)["payment_id"]
    settle(client, buyer, payment_id, "pending")
    old_invoice = payment(payment_id).external_id

    gateway = MockGatewayAdapter(MockPaymentProvider())
    app.dependency_overrides[get_mock_gateway] = lambda: gateway
    try:
        body = settle(client, buyer, payment_id, "success")
    finally:
        app.dependency_overrides.pop(get_mock_gateway, None)

    new_invoice = payment(payment_id).external_id
    assert body["status"] == "success"
    assert new_invoice is not None and new_invoice != old_invoice
    assert gateway.get_status(new_invoice) == "success"
    assert me(client, buyer)["plan_code"] == "premium"


def test_mock_result_can_be_disabled(
    client: TestClient, buyer: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    payment_id = checkout(client, buyer)["payment_id"]
    monkeypatch.setattr(settings, "payments_mock_enabled", False)

    assert_error(mock_result(client, buyer, payment_id, "success"), 404, "mock_payments_disabled")
    assert payment(payment_id).status == "created"


def test_observer_failure_rolls_back_payment_and_subscription(
    client: TestClient, buyer: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    payment_id = checkout(client, buyer)["payment_id"]

    def explode(self: NotificationService, event: DomainEvent, session: Session) -> None:
        raise RuntimeError("notification storage is down")

    monkeypatch.setattr(NotificationService, "handle", explode)
    with pytest.raises(RuntimeError, match="notification storage is down"):
        mock_result(client, buyer, payment_id, "success")

    assert (payment(payment_id).status, payment(payment_id).paid_at) == ("created", None)
    assert rows(Subscription) == []
    assert rows(Notification) == []

    monkeypatch.undo()
    assert settle(client, buyer, payment_id, "success")["status"] == "success"
    assert me(client, buyer)["plan_code"] == "premium"
    assert notification_kinds() == ["subscription_activated"]
