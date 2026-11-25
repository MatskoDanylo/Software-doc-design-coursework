from collections import Counter
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.demo_activity import (
    DEMO_DAYS, DEMO_PASSWORD, DEMO_USERS, PREMIUM_DAYS, DemoActivitySummary, demo_emails, seed_demo_activity,
)
from app.models import (
    Favorite, Payment, PaymentStatus, Subscription, SubscriptionStatus, Title, TitleStats, User, WatchHistory,
)
from app.repositories.report_repository import ReportRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.title_stats_repository import TitleStatsRepository
from app.seed import main, seed_demo_catalog
from app.services.reports import ReportParams, SubscriptionRevenueReport, UserActivityReport
from tests.factories import add_history, make_user
from tests.helpers import bearer, login

NOW = datetime(2026, 11, 25, 9, 30, tzinfo=UTC)


def run(now: datetime = NOW) -> DemoActivitySummary:
    with SessionLocal() as session, session.begin():
        seed_demo_catalog(session)
        return seed_demo_activity(session, now=now)


def counts() -> dict[str, int]:
    with SessionLocal() as session:
        return {
            model.__tablename__: session.scalar(select(func.count()).select_from(model)) or 0
            for model in (User, WatchHistory, Favorite, Payment, Subscription, TitleStats)
        }


@pytest.fixture
def demo(seeded: None) -> DemoActivitySummary:
    return run()


def test_creates_demo_users_with_shared_password(client: TestClient, demo: DemoActivitySummary) -> None:
    with SessionLocal() as session:
        users = session.scalars(select(User).where(User.email.in_(demo_emails())).order_by(User.email)).all()

    assert demo.users == len(users) == DEMO_USERS
    assert users[0].email == "demo.user01@example.com"
    assert all(NOW - timedelta(days=DEMO_DAYS + 1) <= u.created_at <= NOW for u in users)
    assert len({u.profile.display_name for u in users}) == DEMO_USERS
    assert login(client, "demo.user01@example.com", DEMO_PASSWORD).status_code == 200


def test_rerun_recreates_the_same_data(demo: DemoActivitySummary) -> None:
    before = counts()

    assert run() == demo
    assert counts() == before


def test_rerun_keeps_users_outside_the_demo_list(demo: DemoActivitySummary) -> None:
    with SessionLocal() as session, session.begin():
        real = make_user(session, "demo.username@example.com")
        title = session.scalars(select(Title).order_by(Title.id)).first()
        assert title is not None
        add_history(session, real.id, title, finished=True)

    run()

    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == "demo.username@example.com"))
        assert user is not None
        assert session.scalar(select(func.count()).select_from(WatchHistory).where(WatchHistory.user_id == user.id)) == 1
        assert session.scalar(select(func.count()).select_from(User)) == DEMO_USERS + 2


def test_history_follows_registration(demo: DemoActivitySummary) -> None:
    with SessionLocal() as session:
        rows = session.execute(
            select(WatchHistory.last_watched, WatchHistory.progress_sec, User.created_at)
            .join(User, User.id == WatchHistory.user_id)
        ).all()

    assert len(rows) == demo.history
    assert all(created <= watched <= NOW and progress > 0 for watched, progress, created in rows)
    assert demo.favorites > DEMO_USERS


def test_payments_and_subscriptions_are_consistent(demo: DemoActivitySummary) -> None:
    with SessionLocal() as session:
        payments = session.scalars(select(Payment)).all()
        subscriptions = session.scalars(select(Subscription)).all()

    assert {p.status for p in payments} == {"success", "pending", "failed"}
    assert all((p.paid_at is not None) == (p.status == PaymentStatus.SUCCESS) for p in payments)
    assert len({p.external_id for p in payments}) == len(payments)
    successes = Counter(p.user_id for p in payments if p.status == PaymentStatus.SUCCESS)
    assert {s.user_id for s in subscriptions} == set(successes)
    for sub in subscriptions:
        assert sub.expires_at == sub.started_at + timedelta(days=PREMIUM_DAYS * successes[sub.user_id])
        assert (sub.status == SubscriptionStatus.ACTIVE) == (sub.expires_at > NOW)
    active = sum(s.status == SubscriptionStatus.ACTIVE for s in subscriptions)
    assert demo.active_premium == active > 0
    assert demo.payments == dict(Counter(p.status for p in payments))


def weekly(values: list[float]) -> list[float]:
    return [sum(values[i:i + 7]) for i in range(0, len(values), 7)]


@pytest.mark.parametrize("timezone", ["UTC", "Europe/Kyiv"])
def test_charts_have_no_empty_periods(demo: DemoActivitySummary, timezone: str) -> None:
    today = NOW.date()
    params = ReportParams(date_from=today - timedelta(days=DEMO_DAYS), date_to=today - timedelta(days=1),
                          timezone=timezone)
    with SessionLocal() as session:
        source = ReportRepository(session)
        activity = UserActivityReport(source, lambda tz: today).generate(params).sections[0].rows
        revenue = SubscriptionRevenueReport(source, lambda tz: today).generate(params).sections[0].rows

    assert len(activity) == DEMO_DAYS
    assert all(row["active_users"] > 0 for row in activity)
    assert all(week > 0 for week in weekly([row["registrations"] for row in activity]))
    assert all(week > 0 for week in weekly([row["revenue"] for row in revenue]))


def test_title_stats_are_rebuilt(demo: DemoActivitySummary) -> None:
    before = counts()["title_stats"]
    with SessionLocal() as session, session.begin():
        totals = TitleStatsRepository(session).rebuild()

    assert before == demo.stats.titles == totals.titles > 0
    assert demo.stats == totals


def test_demo_user_gets_personal_recommendations(client: TestClient, demo: DemoActivitySummary) -> None:
    headers = bearer(login(client, "demo.user01@example.com", DEMO_PASSWORD).json()["access_token"])
    with SessionLocal() as session:
        watched = set(session.scalars(
            select(WatchHistory.title_id).join(User).where(User.email == "demo.user01@example.com")
        ))

    body = client.get("/api/recommendations", headers=headers).json()

    assert body["strategy"] == "hybrid"
    assert body["items"] and not watched & {item["id"] for item in body["items"]}


def test_admin_resolves_a_demo_pending_payment(client: TestClient, admin_headers: dict[str, str]) -> None:
    now = datetime.now(UTC)
    run(now)
    with SessionLocal() as session:
        pending = session.scalars(
            select(Payment).where(Payment.status == PaymentStatus.PENDING).order_by(Payment.id)
        ).first()
        assert pending is not None
        payment_id, user_id, demo_invoice = pending.id, pending.user_id, pending.external_id

    r = client.post(f"/api/admin/payments/{payment_id}/resolve", json={"outcome": "success"}, headers=admin_headers)

    assert r.status_code == 200, r.text
    assert r.json()["status"] == "success"
    with SessionLocal() as session:
        payment = session.get_one(Payment, payment_id)
        assert payment.paid_at is not None
        assert payment.external_id not in (None, demo_invoice)
        active = SubscriptionRepository(session).get_active(user_id, datetime.now(UTC))
        assert active is not None and active.plan.code == "premium"


def test_seed_cli_prints_demo_credentials(capsys: pytest.CaptureFixture[str]) -> None:
    main(["--demo-activity"])

    out = capsys.readouterr().out
    assert "Demo catalog: 12 genres, 31 titles" in out
    assert f"Demo activity: {DEMO_USERS} users" in out
    assert "demo.user01@example.com ... demo.user40@example.com, password demo12345" in out
    assert counts()["users"] == DEMO_USERS + 1
