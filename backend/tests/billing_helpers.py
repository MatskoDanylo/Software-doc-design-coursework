from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import Notification, Payment, Subscription


def checkout(client: TestClient, headers: dict[str, str], plan_code: str = "premium") -> dict[str, Any]:
    r = client.post("/api/billing/checkout", json={"plan_code": plan_code}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def mock_result(client: TestClient, headers: dict[str, str], payment_id: int, outcome: str) -> Response:
    return client.post(f"/api/billing/payments/{payment_id}/mock-result", json={"outcome": outcome}, headers=headers)


def settle(client: TestClient, headers: dict[str, str], payment_id: int, outcome: str) -> dict[str, Any]:
    r = mock_result(client, headers, payment_id, outcome)
    assert r.status_code == 200, r.text
    return r.json()


def me(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    return client.get("/api/users/me", headers=headers).json()["subscription"]


def rows[T: (Payment, Subscription, Notification)](model: type[T]) -> list[T]:
    with SessionLocal() as session:
        return list(session.scalars(select(model).order_by(model.id)))


def notification_kinds() -> list[str]:
    return [n.kind for n in rows(Notification)]


def payment(payment_id: int) -> Payment:
    with SessionLocal() as session:
        found = session.get(Payment, payment_id)
        assert found is not None
        return found


def days_left(expires_at: str) -> timedelta:
    return datetime.fromisoformat(expires_at) - datetime.now(UTC)
