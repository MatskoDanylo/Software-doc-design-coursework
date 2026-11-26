from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from typing import Any, ClassVar

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.models import PaymentStatus, Plan, PlanCode, SubscriptionStatus, TitleKind, User, VideoAsset, VideoStatus
from app.repositories.report_repository import ReportRepository
from app.services.dashboard_service import DashboardService
from app.services.reports import (
    GroupBy,
    PopularTitlesReport,
    Report,
    ReportGenerator,
    ReportParams,
    SubscriptionRevenueReport,
    UserActivityReport,
)
from tests.factories import (
    add_favorite,
    add_history,
    add_payment,
    add_season,
    add_subscription,
    make_genre,
    make_title,
    make_user,
)

TODAY = date(2026, 11, 25)


def at(month: int, day: int, hour: int = 12, minute: int = 0, second: int = 0, year: int = 2026) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


type GeneratorFactory = Callable[[ReportRepository, Callable[[str], date]], ReportGenerator[Any, Any]]


def generate(factory: GeneratorFactory, **params: Any) -> Report:
    with SessionLocal() as session:
        return factory(ReportRepository(session), lambda tz: TODAY).generate(ReportParams(**params))


def section(report: Report, key: str) -> list[dict[str, Any]]:
    return next(s.rows for s in report.sections if s.key == key)


def summary(report: Report) -> dict[str, Any]:
    return {item.key: item.value for item in report.summary}


@pytest.fixture
def session(seeded: None) -> Iterator[Session]:
    with SessionLocal() as session, session.begin():
        yield session


@contextmanager
def committed() -> Iterator[Session]:
    with SessionLocal() as session, session.begin():
        yield session


def admin(session: Session) -> User:
    user = session.scalar(select(User).where(User.email == settings.admin_email))
    assert user is not None
    return user


def premium(session: Session) -> Plan:
    plan = session.scalar(select(Plan).where(Plan.code == PlanCode.PREMIUM.value))
    assert plan is not None
    return plan


class TestUserActivity:
    @pytest.fixture(autouse=True)
    def data(self, seeded: None) -> None:
        with committed() as session:
            heat, ronin = make_title(session, "Heat"), make_title(session, "Ronin")
            u1 = make_user(session, "u1@example.com", created_at=at(11, 1, 10))
            u2 = make_user(session, "u2@example.com", created_at=at(11, 3, 23, 59, 59))
            u3 = make_user(session, "u3@example.com", created_at=at(11, 4, 0))
            add_history(session, u1.id, heat, progress_sec=600, finished=True, last_watched=at(11, 1))
            add_history(session, u1.id, ronin, progress_sec=300, last_watched=at(11, 2))
            add_history(session, u2.id, heat, progress_sec=900, finished=True, last_watched=at(11, 2, 13))
            add_history(session, u3.id, heat, progress_sec=100, last_watched=at(11, 4, 0))
            add_history(session, admin(session).id, heat, progress_sec=5000, last_watched=at(11, 2))

    def test_daily_series_counts_registrations_activity_and_watch_time(self) -> None:
        report = generate(UserActivityReport, date_from=date(2026, 11, 1), date_to=date(2026, 11, 3))

        assert section(report, "activity") == [
            {"bucket": date(2026, 11, 1), "registrations": 1, "active_users": 1, "watch_minutes": 10.0},
            {"bucket": date(2026, 11, 2), "registrations": 0, "active_users": 2, "watch_minutes": 20.0},
            {"bucket": date(2026, 11, 3), "registrations": 1, "active_users": 0, "watch_minutes": 0.0},
        ]
        assert summary(report) == {
            "new_users": 2,
            "active_users": 2,
            "watch_hours": 0.5,
            "avg_progress_min": 10.0,
            "completion_rate": 66.7,
        }

    def test_monthly_grouping_fills_empty_months(self) -> None:
        report = generate(
            UserActivityReport, date_from=date(2026, 10, 1), date_to=date(2026, 11, 30), group_by=GroupBy.MONTH
        )

        assert section(report, "activity") == [
            {"bucket": date(2026, 10, 1), "registrations": 0, "active_users": 0, "watch_minutes": 0.0},
            {"bucket": date(2026, 11, 1), "registrations": 3, "active_users": 3, "watch_minutes": 31.7},
        ]

    def test_period_end_includes_the_last_second_of_date_to_only(self) -> None:
        report = generate(UserActivityReport, date_from=date(2026, 11, 3), date_to=date(2026, 11, 3))

        assert summary(report)["new_users"] == 1


class TestTimezone:
    @pytest.fixture(autouse=True)
    def data(self, seeded: None) -> None:
        with committed() as session:
            make_user(session, "late@example.com", created_at=at(11, 10, 23, 30))

    @pytest.mark.parametrize(
        ("timezone", "expected"),
        [
            ("Europe/Kyiv", {date(2026, 11, 10): 0, date(2026, 11, 11): 1}),
            ("UTC", {date(2026, 11, 10): 1, date(2026, 11, 11): 0}),
        ],
    )
    def test_buckets_follow_the_report_timezone(self, timezone: str, expected: dict[date, int]) -> None:
        report = generate(
            UserActivityReport, date_from=date(2026, 11, 10), date_to=date(2026, 11, 11), timezone=timezone
        )

        assert {row["bucket"]: row["registrations"] for row in section(report, "activity")} == expected
        assert report.timezone == timezone

    @pytest.mark.parametrize(("timezone", "new_users"), [("Europe/Kyiv", 0), ("UTC", 1)])
    def test_period_bounds_follow_the_report_timezone(self, timezone: str, new_users: int) -> None:
        report = generate(
            UserActivityReport, date_from=date(2026, 11, 10), date_to=date(2026, 11, 10), timezone=timezone
        )

        assert summary(report)["new_users"] == new_users


class TestPopularTitles:
    @pytest.fixture(autouse=True)
    def data(self, seeded: None) -> None:
        with committed() as session:
            drama, comedy = make_genre(session, "Драма"), make_genre(session, "Комедія")
            a = make_title(session, "A", [drama])
            b = make_title(session, "B", [drama, comedy], kind=TitleKind.SERIES.value)
            c = make_title(session, "C", [comedy])
            make_title(session, "D", [drama])
            u1, u2 = make_user(session, "u1@example.com"), make_user(session, "u2@example.com")
            add_history(session, u1.id, a, finished=True, last_watched=at(11, 5))
            add_history(session, u2.id, a, last_watched=at(11, 6))
            add_history(session, u1.id, b, last_watched=at(11, 7))
            add_history(session, u2.id, b, finished=True, last_watched=at(10, 20))
            add_favorite(session, u1.id, a, added_at=at(11, 5))
            add_favorite(session, u2.id, c, added_at=at(11, 8))
            add_favorite(session, u1.id, c, added_at=at(10, 1))

    def test_ranks_titles_and_genres_within_the_period(self) -> None:
        report = generate(PopularTitlesReport, date_from=date(2026, 11, 1), date_to=date(2026, 11, 30))

        titles = section(report, "titles")
        assert [(t["rank"], t["name"], t["viewers"], t["completions"], t["favorites"]) for t in titles] == [
            (1, "A", 2, 1, 1),
            (2, "B", 1, 0, 0),
            (3, "C", 0, 0, 1),
        ]
        assert (titles[1]["kind"], titles[1]["genres"]) == ("series", "Драма, Комедія")
        assert section(report, "genres") == [
            {"genre": "Драма", "titles": 2, "viewers": 3, "completions": 1, "favorites": 1},
            {"genre": "Комедія", "titles": 2, "viewers": 1, "completions": 0, "favorites": 1},
        ]
        assert summary(report) == {
            "total_views": 3,
            "total_completions": 1,
            "total_favorites": 2,
            "top_title": "A",
            "top_genre": "Драма",
        }

    def test_top_limit_hook_trims_titles_but_not_genres(self) -> None:
        class TopOne(PopularTitlesReport):
            TOP_LIMIT: ClassVar[int] = 1

        report = generate(TopOne, date_from=date(2026, 11, 1), date_to=date(2026, 11, 30))

        assert [t["name"] for t in section(report, "titles")] == ["A"]
        assert len(section(report, "genres")) == 2

    def test_empty_period_has_empty_sections(self) -> None:
        report = generate(PopularTitlesReport, date_from=date(2026, 1, 1), date_to=date(2026, 1, 31))

        assert section(report, "titles") == [] and section(report, "genres") == []
        assert summary(report)["top_title"] is None


class TestRevenue:
    @pytest.fixture(autouse=True)
    def data(self, seeded: None) -> None:
        with committed() as session:
            plan = premium(session)
            u1, u2, u3 = (make_user(session, f"u{i}@example.com", created_at=at(10, 1)) for i in (1, 2, 3))
            add_payment(session, u1.id, plan, PaymentStatus.SUCCESS, at(11, 1, 10), paid_at=at(11, 1, 10, 5))
            add_payment(session, u2.id, plan, PaymentStatus.SUCCESS, at(11, 1, 12), paid_at=at(11, 1, 12, 1))
            add_payment(session, u1.id, plan, PaymentStatus.SUCCESS, at(11, 15), paid_at=at(11, 15, 12, 1))
            add_payment(session, u3.id, plan, PaymentStatus.FAILED, at(11, 2))
            add_payment(session, u3.id, plan, PaymentStatus.PENDING, at(11, 3))
            add_payment(session, u2.id, plan, PaymentStatus.SUCCESS, at(10, 31, 22), paid_at=at(10, 31, 23))
            add_subscription(session, u1.id, plan, at(11, 15), at(1, 15, year=2099))
            add_subscription(session, u2.id, plan, at(10, 1), at(11, 1), status=SubscriptionStatus.EXPIRED)

    def test_daily_revenue_statuses_and_conversion(self) -> None:
        report = generate(SubscriptionRevenueReport, date_from=date(2026, 11, 1), date_to=date(2026, 11, 30))

        revenue = section(report, "revenue")
        assert len(revenue) == 30
        assert revenue[0] == {"bucket": date(2026, 11, 1), "revenue": 198.0, "payments": 2}
        assert revenue[14] == {"bucket": date(2026, 11, 15), "revenue": 99.0, "payments": 1}
        assert sum(r["payments"] for r in revenue) == 3
        assert section(report, "statuses") == [
            {"status": "created", "count": 0},
            {"status": "pending", "count": 1},
            {"status": "success", "count": 3},
            {"status": "failed", "count": 1},
        ]
        assert summary(report) == {
            "total_revenue": 297.0,
            "successful_payments": 3,
            "paying_users": 2,
            "active_premium": 1,
            "conversion": 66.7,
        }

    def test_monthly_revenue(self) -> None:
        report = generate(
            SubscriptionRevenueReport, date_from=date(2026, 10, 1), date_to=date(2026, 11, 30), group_by=GroupBy.MONTH
        )

        assert section(report, "revenue") == [
            {"bucket": date(2026, 10, 1), "revenue": 99.0, "payments": 1},
            {"bucket": date(2026, 11, 1), "revenue": 297.0, "payments": 3},
        ]
        assert summary(report)["paying_users"] == 2

    def test_default_period_is_ninety_days(self) -> None:
        report = generate(SubscriptionRevenueReport)

        assert (report.date_from, report.date_to) == (date(2026, 8, 28), TODAY)
        assert len(section(report, "revenue")) == 90


def test_dashboard_kpis(session: Session) -> None:
    now = datetime.now(UTC)
    plan = premium(session)
    u1, u2 = make_user(session, "u1@example.com"), make_user(session, "u2@example.com")
    movie, failed, _ = (make_title(session, n) for n in ("Ready", "Broken", "No video"))
    series, draft = (make_title(session, n, kind=TitleKind.SERIES.value) for n in ("Series", "Draft"))
    episode = add_season(session, series, 1, ["Pilot"]).episodes[0]
    draft_episode = add_season(session, draft, 1, ["Pilot"]).episodes[0]
    session.add_all(
        [
            VideoAsset(title_id=movie.id, status=VideoStatus.READY.value, hls_path="hls/1/master.m3u8"),
            VideoAsset(title_id=failed.id, status=VideoStatus.FAILED.value),
            VideoAsset(episode_id=episode.id, status=VideoStatus.READY.value, hls_path="hls/3/master.m3u8"),
            VideoAsset(episode_id=draft_episode.id, status=VideoStatus.PENDING.value),
        ]
    )
    add_history(session, u1.id, movie, last_watched=now - timedelta(days=1))
    add_history(session, u2.id, movie, last_watched=now - timedelta(days=10))
    add_history(session, admin(session).id, movie, last_watched=now - timedelta(days=1))
    add_payment(session, u1.id, plan, PaymentStatus.SUCCESS, now - timedelta(days=5), paid_at=now - timedelta(days=5))
    add_payment(session, u2.id, plan, PaymentStatus.SUCCESS, now - timedelta(days=40), paid_at=now - timedelta(days=40))
    add_payment(session, u2.id, plan, PaymentStatus.FAILED, now - timedelta(days=1))
    add_subscription(session, u1.id, plan, now - timedelta(days=5), now + timedelta(days=25))
    session.flush()

    kpis = DashboardService(ReportRepository(session)).kpis()

    assert (kpis.total_users, kpis.active_users_7d, kpis.active_premium, kpis.revenue_30d, kpis.titles_with_video) == (
        2,
        1,
        1,
        99.0,
        2,
    )
