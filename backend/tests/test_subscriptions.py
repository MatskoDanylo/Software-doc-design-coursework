from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.errors import NotFoundError, UnprocessableError
from app.models import PlanCode, Subscription, SubscriptionStatus, User
from app.patterns.plan_factory import default_plan_registry
from app.repositories.plans import PlanRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.users import UserRepository
from app.services.subscription_service import SubscriptionService
from app.tools.grant_premium import main as grant_premium_main
from tests.helpers import register

NOW = datetime(2026, 11, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def user_email(client: TestClient) -> str:
    register(client, "viewer@example.com")
    return "viewer@example.com"


@contextmanager
def service_for(email: str, now: datetime = NOW) -> Iterator[tuple[SubscriptionService, User]]:
    with SessionLocal() as session, session.begin():
        user = UserRepository(session).get_by_email(email)
        assert user is not None
        service = SubscriptionService(
            SubscriptionRepository(session), PlanRepository(session), default_plan_registry(30), clock=lambda: now
        )
        yield service, user


def subscriptions(email: str) -> list[Subscription]:
    with SessionLocal() as session:
        user = UserRepository(session).get_by_email(email)
        assert user is not None
        return list(session.scalars(select(Subscription).where(Subscription.user_id == user.id)))


def test_user_without_subscription_is_on_free_plan(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        policy = service.policy_for(user)

    assert (policy.plan_code, policy.max_height, policy.ads_enabled) == ("free", 720, True)


def test_grant_creates_active_premium_subscription(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user, PlanCode.PREMIUM, 30)
        policy = service.policy_for(user)

    assert (policy.plan_code, policy.max_height, policy.ads_enabled) == ("premium", 1080, False)
    [subscription] = subscriptions(user_email)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.expires_at == NOW + timedelta(days=30)


def test_grant_extends_active_premium_instead_of_duplicating(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user, PlanCode.PREMIUM, 30)
    with service_for(user_email, NOW + timedelta(days=10)) as (service, user):
        service.grant(user, PlanCode.PREMIUM, 7)

    [subscription] = subscriptions(user_email)
    assert subscription.expires_at == NOW + timedelta(days=37)


def test_expired_subscription_is_ignored(seeded: None, user_email: str) -> None:
    with service_for(user_email) as (service, user):
        service.grant(user, PlanCode.PREMIUM, 1)
    with service_for(user_email, NOW + timedelta(days=2)) as (service, user):
        assert service.policy_for(user).plan_code == "free"


def test_grant_validates_duration_and_seeded_plans(user_email: str) -> None:
    with service_for(user_email) as (service, user):
        with pytest.raises(UnprocessableError):
            service.grant(user, PlanCode.PREMIUM, 0)
        with pytest.raises(NotFoundError, match="python -m app.seed"):
            service.grant(user, PlanCode.PREMIUM, 30)


def test_grant_premium_cli(seeded: None, user_email: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert grant_premium_main(["VIEWER@example.com", "--days", "14"]) == 0

    assert "Premium active for viewer@example.com until" in capsys.readouterr().out
    [subscription] = subscriptions(user_email)
    assert subscription.expires_at is not None
    assert timedelta(days=13) < subscription.expires_at - datetime.now(UTC) <= timedelta(days=14)


def test_grant_premium_cli_reports_unknown_user(seeded: None, capsys: pytest.CaptureFixture[str]) -> None:
    assert grant_premium_main(["nobody@example.com"]) == 1
    assert "nobody@example.com not found" in capsys.readouterr().out


def test_grant_premium_cli_reports_missing_plans(user_email: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert grant_premium_main([user_email]) == 1
    assert "python -m app.seed" in capsys.readouterr().out
