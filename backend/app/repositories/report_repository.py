from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import ColumnElement, Date, DateTime, and_, bindparam, cast, func, or_, select, union
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.models import (
    Episode, Favorite, Payment, PaymentStatus, Plan, PlanCode, Role, Season, Subscription, SubscriptionStatus, Title,
    User, VideoAsset, VideoStatus, WatchHistory,
)
from app.services.reports import BucketActivity, Period, RevenueBucket, TitleActivity, WatchTotals


type TimestampColumn = InstrumentedAttribute[datetime] | InstrumentedAttribute[datetime | None]


def _local_midnight(period: Period, day: date) -> ColumnElement[datetime]:
    naive = bindparam(None, datetime.combine(day, time()), type_=DateTime(timezone=False))
    return func.timezone(period.timezone, naive)


def in_period(column: TimestampColumn, period: Period) -> ColumnElement[bool]:
    start = _local_midnight(period, period.date_from)
    end = _local_midnight(period, period.date_to + timedelta(days=1))
    return and_(column >= start, column < end)


def bucket(column: TimestampColumn, period: Period) -> ColumnElement[date]:
    return cast(func.date_trunc(period.group_by.value, func.timezone(period.timezone, column)), Date)


def _customer() -> ColumnElement[bool]:
    return User.role != Role.ADMIN.value


class ReportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def today(self, timezone: str) -> date:
        today: date = self.session.execute(select(cast(func.timezone(timezone, func.now()), Date))).scalar_one()
        return today

    def title_activity(self, period: Period) -> Sequence[TitleActivity]:
        views = (
            select(
                WatchHistory.title_id,
                func.count(WatchHistory.user_id.distinct()).label("viewers"),
                func.count().filter(WatchHistory.finished.is_(True)).label("completions"),
            )
            .where(in_period(WatchHistory.last_watched, period))
            .group_by(WatchHistory.title_id)
            .subquery()
        )
        favorites = (
            select(Favorite.title_id, func.count().label("favorites"))
            .where(in_period(Favorite.added_at, period))
            .group_by(Favorite.title_id)
            .subquery()
        )
        rows = self.session.execute(
            select(Title, func.coalesce(views.c.viewers, 0), func.coalesce(views.c.completions, 0),
                   func.coalesce(favorites.c.favorites, 0))
            .outerjoin(views, views.c.title_id == Title.id)
            .outerjoin(favorites, favorites.c.title_id == Title.id)
            .where(or_(views.c.title_id.is_not(None), favorites.c.title_id.is_not(None)))
        ).all()
        return [
            TitleActivity(title.id, title.name, title.kind, tuple(g.name for g in title.genres),
                          viewers, completions, favorite_count)
            for title, viewers, completions, favorite_count in rows
        ]

    def registrations(self, period: Period) -> Mapping[date, int]:
        day = bucket(User.created_at, period)
        rows = self.session.execute(
            select(day, func.count()).where(in_period(User.created_at, period), _customer()).group_by(day)
        )
        return {key: count for key, count in rows}

    def activity_by_bucket(self, period: Period) -> Mapping[date, BucketActivity]:
        day = bucket(WatchHistory.last_watched, period)
        rows = self.session.execute(
            select(day, func.count(WatchHistory.user_id.distinct()), func.coalesce(func.sum(WatchHistory.progress_sec), 0))
            .join(User, User.id == WatchHistory.user_id)
            .where(in_period(WatchHistory.last_watched, period), _customer())
            .group_by(day)
        )
        return {key: BucketActivity(users, seconds) for key, users, seconds in rows}

    def watch_totals(self, period: Period) -> WatchTotals:
        entries, seconds, finished, users = self.session.execute(
            select(
                func.count(),
                func.coalesce(func.sum(WatchHistory.progress_sec), 0),
                func.count().filter(WatchHistory.finished.is_(True)),
                func.count(WatchHistory.user_id.distinct()),
            )
            .join(User, User.id == WatchHistory.user_id)
            .where(in_period(WatchHistory.last_watched, period), _customer())
        ).one()
        return WatchTotals(entries=entries, watch_seconds=seconds, finished=finished, active_users=users)

    def revenue_by_bucket(self, period: Period) -> Mapping[date, RevenueBucket]:
        day = bucket(Payment.paid_at, period)
        rows = self.session.execute(
            select(day, func.sum(Payment.amount), func.count())
            .where(Payment.status == PaymentStatus.SUCCESS.value, in_period(Payment.paid_at, period))
            .group_by(day)
        )
        return {key: RevenueBucket(amount, count) for key, amount, count in rows}

    def payment_status_counts(self, period: Period) -> Mapping[str, int]:
        rows = self.session.execute(
            select(Payment.status, func.count()).where(in_period(Payment.created_at, period)).group_by(Payment.status)
        )
        return {status: count for status, count in rows}

    def paying_users(self, period: Period) -> int:
        return self.session.scalar(
            select(func.count(Payment.user_id.distinct()))
            .where(Payment.status == PaymentStatus.SUCCESS.value, in_period(Payment.paid_at, period))
        ) or 0

    def registered_users(self, period: Period) -> int:
        end = _local_midnight(period, period.date_to + timedelta(days=1))
        return self.session.scalar(
            select(func.count()).select_from(User).where(User.created_at < end, _customer())
        ) or 0

    def active_premium(self) -> int:
        return self.session.scalar(
            select(func.count(Subscription.user_id.distinct()))
            .join(Plan, Plan.id == Subscription.plan_id)
            .where(
                Plan.code == PlanCode.PREMIUM.value,
                Subscription.status.in_([SubscriptionStatus.ACTIVE.value, SubscriptionStatus.CANCELLED.value]),
                or_(Subscription.expires_at.is_(None), Subscription.expires_at > func.now()),
            )
        ) or 0

    def total_users(self) -> int:
        return self.session.scalar(select(func.count()).select_from(User).where(_customer())) or 0

    def active_users_since(self, days: int) -> int:
        return self.session.scalar(
            select(func.count(WatchHistory.user_id.distinct()))
            .join(User, User.id == WatchHistory.user_id)
            .where(WatchHistory.last_watched >= func.now() - timedelta(days=days), _customer())
        ) or 0

    def revenue_since(self, days: int) -> Decimal:
        return self.session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.status == PaymentStatus.SUCCESS.value, Payment.paid_at >= func.now() - timedelta(days=days))
        ) or Decimal("0")

    def titles_with_video(self) -> int:
        ready = VideoAsset.status == VideoStatus.READY.value
        movies = select(VideoAsset.title_id.label("title_id")).where(ready, VideoAsset.title_id.is_not(None))
        series = (
            select(Season.title_id.label("title_id"))
            .join(Episode, Episode.season_id == Season.id)
            .join(VideoAsset, VideoAsset.episode_id == Episode.id)
            .where(ready)
        )
        titles = union(movies, series).subquery()
        return self.session.scalar(select(func.count()).select_from(titles)) or 0
