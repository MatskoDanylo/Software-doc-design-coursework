from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.events import SubscriptionActivated
from app.models import PlanCode, Subscription, SubscriptionStatus, User
from app.patterns.plan_factory import default_plan_registry
from app.repositories.plans import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.users import UserRepository
from app.services.subscription_service import FREE_INFO, SubscriptionInfo, SubscriptionService
from app.tools.grant_premium import main as grant_premium_main
from tests.helpers import RecordingPublisher, assert_error, register

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def user_email(client: TestClient) -> str:
    register(client, "viewer@example.com")
    return "viewer@example.com"


@contextmanager
def service_for(
    email: str, now: datetime = NOW, publisher: RecordingPublisher | None = None
) -> Iterator[tuple[SubscriptionService, User]]:
    with SessionLocal() as session, session.begin():
        user = UserRepository(session).get_by_email(email)
        assert user is not None
        service = SubscriptionService(
            SubscriptionRepository(session),
            PlanRepository(session),
            default_plan_registry(30),
            publisher or RecordingPublisher(),
            clock=lambda: now,
        )
        yield service, user


def subscriptions(email: str) -> list[Subscription]:
    with SessionLocal() as session:
        user = UserRepository(session).get_by_email(email)
        assert user is not None
        return list(
            session.scalars(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.id))
        )


def test_user_without_subscription_is_on_free_plan(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        policy = service.policy_for(user)
        summary = service.summary(user.id)

    assert (policy.plan_code, policy.max_height, policy.ads_enabled) == ("free", 720, True)
    assert summary == FREE_INFO


def test_grant_creates_active_premium_subscription(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
        policy = service.policy_for(user)

    assert (policy.plan_code, policy.max_height, policy.ads_enabled) == ("premium", 1080, False)
    [subscription] = subscriptions(user_email)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.expires_at == NOW + timedelta(days=30)


def test_grant_without_days_uses_plan_policy_duration(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM)

    [subscription] = subscriptions(user_email)
    assert subscription.expires_at == NOW + timedelta(days=30)


def test_grant_publishes_subscription_activated(seeded: None, user_email: str) -> None:
    publisher = RecordingPublisher()
    with service_for(user_email, publisher=publisher) as (service, user):
        subscription = service.grant(user.id, PlanCode.PREMIUM, 30)
        expected = SubscriptionActivated(
            user_id=user.id, subscription_id=subscription.id, plan_code="premium", expires_at=NOW + timedelta(days=30)
        )

    assert publisher.events == [expected]


def test_grant_extends_active_premium_instead_of_duplicating(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
    with service_for(user_email, NOW + timedelta(days=10)) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 7)

    [subscription] = subscriptions(user_email)
    assert subscription.expires_at == NOW + timedelta(days=37)


def test_grant_after_expiry_starts_a_new_period(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 1)
    later = NOW + timedelta(days=5)
    with service_for(user_email, later) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)

    assert [s.expires_at for s in subscriptions(user_email)] == [NOW + timedelta(days=1), later + timedelta(days=30)]


def test_expired_subscription_is_ignored(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 1)
    with service_for(user_email, NOW + timedelta(days=2)) as (service, user):
        assert service.policy_for(user).plan_code == "free"


def test_grant_validates_duration_and_seeded_plans(user_email: str) -> None:
    with service_for(user_email) as (service, user):
        with pytest.raises(UnprocessableError):
            service.grant(user.id, PlanCode.PREMIUM, 0)
        with pytest.raises(NotFoundError, match=r"python -m app\.seed"):
            service.grant(user.id, PlanCode.PREMIUM, 30)


def test_free_plan_cannot_be_granted_without_explicit_duration(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user), pytest.raises(UnprocessableError, match="cannot be granted"):
        service.grant(user.id, PlanCode.FREE)


def test_granting_another_plan_expires_the_active_one(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
    later = NOW + timedelta(days=3)
    with service_for(user_email, later) as (service, user):
        service.grant(user.id, PlanCode.FREE, 5)
        assert service.policy_for(user).plan_code == "free"

    premium, free = subscriptions(user_email)
    assert (premium.status, free.status) == (SubscriptionStatus.EXPIRED, SubscriptionStatus.ACTIVE)
    assert free.expires_at == later + timedelta(days=5)


def test_cancelled_subscription_keeps_access_until_expiry(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
        summary = service.cancel(user)

    assert summary == SubscriptionInfo(plan_code="premium", expires_at=NOW + timedelta(days=30), cancelled=True)
    with service_for(user_email, NOW + timedelta(days=29)) as (service, user):
        assert service.policy_for(user).plan_code == "premium"
    with service_for(user_email, NOW + timedelta(days=31)) as (service, user):
        assert service.policy_for(user).plan_code == "free"
    assert subscriptions(user_email)[0].status == SubscriptionStatus.CANCELLED


def test_cancel_is_idempotent(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
        first = service.cancel(user)
        second = service.cancel(user)

    assert first == second


def test_cancel_without_subscription_conflicts(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user), pytest.raises(ConflictError) as exc:
        service.cancel(user)

    assert exc.value.code == "no_active_subscription"


def test_grant_after_cancel_resumes_and_extends(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
        service.cancel(user)
        service.grant(user.id, PlanCode.PREMIUM, 30)
        summary = service.summary(user.id)

    assert summary == SubscriptionInfo(plan_code="premium", expires_at=NOW + timedelta(days=60), cancelled=False)
    assert len(subscriptions(user_email)) == 1


def test_revoke_ends_access_immediately(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user.id, PlanCode.PREMIUM, 30)
        summary = service.revoke(user.id)
        policy = service.policy_for(user)

    assert summary == FREE_INFO
    assert policy.plan_code == "free"
    [subscription] = subscriptions(user_email)
    assert (subscription.status, subscription.expires_at) == (SubscriptionStatus.EXPIRED, NOW)


def test_revoke_without_subscription_is_a_no_op(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        assert service.revoke(user.id) == FREE_INFO

    assert subscriptions(user_email) == []


def test_me_reports_free_plan(client: TestClient, user_headers: dict[str, str]) -> None:
    body = client.get("/api/users/me", headers=user_headers).json()

    assert body["subscription"] == {"plan_code": "free", "expires_at": None, "cancelled": False}


def test_me_reports_premium_and_cancellation(client: TestClient, seeded: None, user_headers: dict[str, str]) -> None:
    grant_premium_main(["user@example.com", "--days", "10"])

    me = client.get("/api/users/me", headers=user_headers).json()["subscription"]
    assert (me["plan_code"], me["cancelled"]) == ("premium", False)
    assert timedelta(days=9) < datetime.fromisoformat(me["expires_at"]) - datetime.now(UTC) <= timedelta(days=10)

    r = client.post("/api/subscriptions/cancel", headers=user_headers)
    assert r.status_code == 200, r.text
    assert r.json() == {**me, "cancelled": True}
    patched = client.patch("/api/users/me", json={"country": "Ukraine"}, headers=user_headers).json()
    assert patched["subscription"] == {**me, "cancelled": True}


def test_cancel_endpoint_requires_subscription_and_auth(client: TestClient, user_headers: dict[str, str]) -> None:
    assert_error(client.post("/api/subscriptions/cancel", headers=user_headers), 409, "no_active_subscription")
    assert client.post("/api/subscriptions/cancel").status_code == 401


def test_grant_premium_cli(seeded: None, user_email: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert grant_premium_main(["VIEWER@example.com", "--days", "14"]) == 0

    assert "Premium active for viewer@example.com until" in capsys.readouterr().out
    [subscription] = subscriptions(user_email)
    assert subscription.expires_at is not None
    assert timedelta(days=13) < subscription.expires_at - datetime.now(UTC) <= timedelta(days=14)


def test_grant_premium_cli_defaults_to_plan_duration(seeded: None, user_email: str) -> None:
    assert grant_premium_main([user_email]) == 0

    [subscription] = subscriptions(user_email)
    assert subscription.expires_at is not None
    assert timedelta(days=29) < subscription.expires_at - datetime.now(UTC) <= timedelta(days=30)


def test_grant_premium_cli_reports_unknown_user(seeded: None, capsys: pytest.CaptureFixture[str]) -> None:
    assert grant_premium_main(["nobody@example.com"]) == 1
    assert "nobody@example.com not found" in capsys.readouterr().out


def test_grant_premium_cli_reports_missing_plans(user_email: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert grant_premium_main([user_email]) == 1
    assert "python -m app.seed" in capsys.readouterr().out
