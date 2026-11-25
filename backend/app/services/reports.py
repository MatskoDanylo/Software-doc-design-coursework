from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar, Protocol, final

from app.core.errors import NotFoundError, UnprocessableError
from app.models import PaymentStatus


class GroupBy(StrEnum):
    DAY = "day"
    MONTH = "month"


type ReportValue = str | int | float | date | None


@dataclass(frozen=True)
class ReportParams:
    date_from: date | None = None
    date_to: date | None = None
    group_by: GroupBy | None = None
    timezone: str = "UTC"


@dataclass(frozen=True)
class Period:
    date_from: date
    date_to: date
    group_by: GroupBy
    timezone: str

    @property
    def days(self) -> int:
        return (self.date_to - self.date_from).days + 1


@dataclass(frozen=True)
class ReportColumn:
    key: str
    label: str


@dataclass(frozen=True)
class ReportSection:
    key: str
    title: str
    columns: tuple[ReportColumn, ...]
    rows: list[dict[str, ReportValue]]


@dataclass(frozen=True)
class SummaryItem:
    key: str
    label: str
    value: ReportValue


@dataclass(frozen=True)
class Report:
    kind: str
    title: str
    date_from: date
    date_to: date
    group_by: GroupBy
    timezone: str
    summary: tuple[SummaryItem, ...]
    sections: tuple[ReportSection, ...]


def fill_buckets(period: Period) -> list[date]:
    if period.group_by is GroupBy.DAY:
        return [period.date_from + timedelta(days=i) for i in range(period.days)]
    buckets, current = [], period.date_from.replace(day=1)
    while current <= period.date_to:
        buckets.append(current)
        current = (current + timedelta(days=32)).replace(day=1)
    return buckets


def percent(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


class ReportGenerator[RowsT, DataT](ABC):
    kind: ClassVar[str]
    title: ClassVar[str]
    MAX_PERIOD_DAYS: ClassVar[int] = 3660

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "generate" in cls.__dict__:
            raise TypeError(f"{cls.__name__} must not override the template method generate()")

    def __init__(self, today: Callable[[str], date]) -> None:
        self.today = today

    @final
    def generate(self, params: ReportParams) -> Report:
        period = self.validate(params)
        rows = self.collect(period)
        data = self.aggregate(rows, period)
        summary = self.summarize(data, period)
        return self.build(data, summary, period)

    def validate(self, params: ReportParams) -> Period:
        default_from, default_to = self.default_period(self.today(params.timezone))
        date_to = params.date_to or default_to
        date_from = params.date_from or date_to - (default_to - default_from)
        if date_from > date_to:
            raise UnprocessableError("date_from must not be later than date_to", code="invalid_period")
        period = Period(date_from, date_to, params.group_by or self.default_group_by(), params.timezone)
        if period.days > self.MAX_PERIOD_DAYS:
            raise UnprocessableError(f"Period must not exceed {self.MAX_PERIOD_DAYS} days", code="period_too_long")
        self.extra_validation(period)
        return period

    @abstractmethod
    def collect(self, period: Period) -> RowsT: ...

    @abstractmethod
    def aggregate(self, rows: RowsT, period: Period) -> DataT: ...

    @abstractmethod
    def summarize(self, data: DataT, period: Period) -> tuple[SummaryItem, ...]: ...

    @abstractmethod
    def sections(self, data: DataT, period: Period) -> tuple[ReportSection, ...]: ...

    def build(self, data: DataT, summary: tuple[SummaryItem, ...], period: Period) -> Report:
        return Report(
            kind=self.kind,
            title=self.title,
            date_from=period.date_from,
            date_to=period.date_to,
            group_by=period.group_by,
            timezone=period.timezone,
            summary=summary,
            sections=self.sections(data, period),
        )

    def default_period(self, today: date) -> tuple[date, date]:
        return today - timedelta(days=29), today

    def default_group_by(self) -> GroupBy:
        return GroupBy.DAY

    def extra_validation(self, period: Period) -> None:
        return None


@dataclass(frozen=True)
class TitleActivity:
    title_id: int
    name: str
    kind: str
    genres: tuple[str, ...]
    viewers: int
    completions: int
    favorites: int


@dataclass(frozen=True)
class GenreActivity:
    genre: str
    titles: int
    viewers: int
    completions: int
    favorites: int


@dataclass(frozen=True)
class PopularTitlesData:
    top_titles: list[TitleActivity]
    genres: list[GenreActivity]
    total_views: int
    total_completions: int
    total_favorites: int


class PopularTitlesSource(Protocol):
    def title_activity(self, period: Period) -> Sequence[TitleActivity]: ...


class PopularTitlesReport(ReportGenerator[Sequence[TitleActivity], PopularTitlesData]):
    kind = "popular-titles"
    title = "Популярні тайтли та жанри"
    TOP_LIMIT: ClassVar[int] = 10

    def __init__(self, source: PopularTitlesSource, today: Callable[[str], date]) -> None:
        super().__init__(today)
        self.source = source

    def collect(self, period: Period) -> Sequence[TitleActivity]:
        return self.source.title_activity(period)

    def aggregate(self, rows: Sequence[TitleActivity], period: Period) -> PopularTitlesData:
        ranked = sorted(rows, key=lambda r: (-r.viewers, -r.completions, -r.favorites, r.name, r.title_id))
        genres: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
        for row in rows:
            for genre in row.genres:
                totals = genres[genre]
                totals[0] += 1
                totals[1] += row.viewers
                totals[2] += row.completions
                totals[3] += row.favorites
        genre_rows = sorted(
            (GenreActivity(name, *values) for name, values in genres.items()),
            key=lambda g: (-g.viewers, -g.completions, -g.favorites, g.genre),
        )
        return PopularTitlesData(
            top_titles=ranked[:self.TOP_LIMIT],
            genres=genre_rows,
            total_views=sum(r.viewers for r in rows),
            total_completions=sum(r.completions for r in rows),
            total_favorites=sum(r.favorites for r in rows),
        )

    def summarize(self, data: PopularTitlesData, period: Period) -> tuple[SummaryItem, ...]:
        return (
            SummaryItem("total_views", "Переглядів", data.total_views),
            SummaryItem("total_completions", "Завершених переглядів", data.total_completions),
            SummaryItem("total_favorites", "Додавань у Вибране", data.total_favorites),
            SummaryItem("top_title", "Найпопулярніший тайтл", data.top_titles[0].name if data.top_titles else None),
            SummaryItem("top_genre", "Найпопулярніший жанр", data.genres[0].genre if data.genres else None),
        )

    def sections(self, data: PopularTitlesData, period: Period) -> tuple[ReportSection, ...]:
        titles = ReportSection(
            key="titles",
            title="Топ тайтлів",
            columns=(
                ReportColumn("rank", "Місце"), ReportColumn("title_id", "ID"), ReportColumn("name", "Назва"),
                ReportColumn("kind", "Тип"), ReportColumn("genres", "Жанри"), ReportColumn("viewers", "Глядачі"),
                ReportColumn("completions", "Завершення"), ReportColumn("favorites", "Вибране"),
            ),
            rows=[
                {"rank": rank, "title_id": t.title_id, "name": t.name, "kind": t.kind, "genres": ", ".join(t.genres),
                 "viewers": t.viewers, "completions": t.completions, "favorites": t.favorites}
                for rank, t in enumerate(data.top_titles, start=1)
            ],
        )
        genres = ReportSection(
            key="genres",
            title="Популярні жанри",
            columns=(
                ReportColumn("genre", "Жанр"), ReportColumn("titles", "Тайтлів"), ReportColumn("viewers", "Глядачі"),
                ReportColumn("completions", "Завершення"), ReportColumn("favorites", "Вибране"),
            ),
            rows=[
                {"genre": g.genre, "titles": g.titles, "viewers": g.viewers, "completions": g.completions,
                 "favorites": g.favorites}
                for g in data.genres
            ],
        )
        return titles, genres


@dataclass(frozen=True)
class BucketActivity:
    active_users: int
    watch_seconds: int


@dataclass(frozen=True)
class WatchTotals:
    entries: int
    watch_seconds: int
    finished: int
    active_users: int


@dataclass(frozen=True)
class UserActivityRows:
    registrations: Mapping[date, int]
    activity: Mapping[date, BucketActivity]
    totals: WatchTotals


@dataclass(frozen=True)
class ActivityPoint:
    bucket: date
    registrations: int
    active_users: int
    watch_minutes: float


@dataclass(frozen=True)
class UserActivityData:
    points: list[ActivityPoint]
    new_users: int
    totals: WatchTotals


class UserActivitySource(Protocol):
    def registrations(self, period: Period) -> Mapping[date, int]: ...

    def activity_by_bucket(self, period: Period) -> Mapping[date, BucketActivity]: ...

    def watch_totals(self, period: Period) -> WatchTotals: ...


class UserActivityReport(ReportGenerator[UserActivityRows, UserActivityData]):
    kind = "user-activity"
    title = "Активність користувачів"
    MAX_DAILY_DAYS: ClassVar[int] = 366

    def __init__(self, source: UserActivitySource, today: Callable[[str], date]) -> None:
        super().__init__(today)
        self.source = source

    def extra_validation(self, period: Period) -> None:
        if period.group_by is GroupBy.DAY and period.days > self.MAX_DAILY_DAYS:
            raise UnprocessableError(
                f"Daily grouping is limited to {self.MAX_DAILY_DAYS} days; use group_by=month",
                code="period_too_long",
            )

    def collect(self, period: Period) -> UserActivityRows:
        return UserActivityRows(
            registrations=self.source.registrations(period),
            activity=self.source.activity_by_bucket(period),
            totals=self.source.watch_totals(period),
        )

    def aggregate(self, rows: UserActivityRows, period: Period) -> UserActivityData:
        idle = BucketActivity(0, 0)
        points = [
            ActivityPoint(
                bucket=bucket,
                registrations=rows.registrations.get(bucket, 0),
                active_users=rows.activity.get(bucket, idle).active_users,
                watch_minutes=round(rows.activity.get(bucket, idle).watch_seconds / 60, 1),
            )
            for bucket in fill_buckets(period)
        ]
        return UserActivityData(points=points, new_users=sum(rows.registrations.values()), totals=rows.totals)

    def summarize(self, data: UserActivityData, period: Period) -> tuple[SummaryItem, ...]:
        totals = data.totals
        average = round(totals.watch_seconds / totals.entries / 60, 1) if totals.entries else 0.0
        return (
            SummaryItem("new_users", "Нових користувачів", data.new_users),
            SummaryItem("active_users", "Активних користувачів", totals.active_users),
            SummaryItem("watch_hours", "Сумарний час перегляду, год", round(totals.watch_seconds / 3600, 1)),
            SummaryItem("avg_progress_min", "Середній прогрес перегляду, хв", average),
            SummaryItem("completion_rate", "Частка завершених переглядів, %", percent(totals.finished, totals.entries)),
        )

    def sections(self, data: UserActivityData, period: Period) -> tuple[ReportSection, ...]:
        return (ReportSection(
            key="activity",
            title="Активність за періодами",
            columns=(
                ReportColumn("bucket", "Період"), ReportColumn("registrations", "Реєстрації"),
                ReportColumn("active_users", "Активні користувачі"), ReportColumn("watch_minutes", "Час перегляду, хв"),
            ),
            rows=[
                {"bucket": p.bucket, "registrations": p.registrations, "active_users": p.active_users,
                 "watch_minutes": p.watch_minutes}
                for p in data.points
            ],
        ),)


@dataclass(frozen=True)
class RevenueBucket:
    amount: Decimal
    payments: int


@dataclass(frozen=True)
class RevenueRows:
    revenue: Mapping[date, RevenueBucket]
    statuses: Mapping[str, int]
    paying_users: int
    registered_users: int
    active_premium: int


@dataclass(frozen=True)
class RevenuePoint:
    bucket: date
    revenue: float
    payments: int


@dataclass(frozen=True)
class RevenueData:
    points: list[RevenuePoint]
    statuses: list[tuple[str, int]]
    total_revenue: Decimal
    successful_payments: int
    paying_users: int
    registered_users: int
    active_premium: int


class RevenueSource(Protocol):
    def revenue_by_bucket(self, period: Period) -> Mapping[date, RevenueBucket]: ...

    def payment_status_counts(self, period: Period) -> Mapping[str, int]: ...

    def paying_users(self, period: Period) -> int: ...

    def registered_users(self, period: Period) -> int: ...

    def active_premium(self) -> int: ...


class SubscriptionRevenueReport(ReportGenerator[RevenueRows, RevenueData]):
    kind = "subscription-revenue"
    title = "Доходи від підписок"

    def __init__(self, source: RevenueSource, today: Callable[[str], date]) -> None:
        super().__init__(today)
        self.source = source

    def default_period(self, today: date) -> tuple[date, date]:
        return today - timedelta(days=89), today

    def collect(self, period: Period) -> RevenueRows:
        return RevenueRows(
            revenue=self.source.revenue_by_bucket(period),
            statuses=self.source.payment_status_counts(period),
            paying_users=self.source.paying_users(period),
            registered_users=self.source.registered_users(period),
            active_premium=self.source.active_premium(),
        )

    def aggregate(self, rows: RevenueRows, period: Period) -> RevenueData:
        empty = RevenueBucket(Decimal("0"), 0)
        points = [
            RevenuePoint(bucket, money(rows.revenue.get(bucket, empty).amount), rows.revenue.get(bucket, empty).payments)
            for bucket in fill_buckets(period)
        ]
        return RevenueData(
            points=points,
            statuses=[(status.value, rows.statuses.get(status.value, 0)) for status in PaymentStatus],
            total_revenue=sum((b.amount for b in rows.revenue.values()), Decimal("0")),
            successful_payments=sum(b.payments for b in rows.revenue.values()),
            paying_users=rows.paying_users,
            registered_users=rows.registered_users,
            active_premium=rows.active_premium,
        )

    def summarize(self, data: RevenueData, period: Period) -> tuple[SummaryItem, ...]:
        return (
            SummaryItem("total_revenue", "Дохід, грн", money(data.total_revenue)),
            SummaryItem("successful_payments", "Успішних платежів", data.successful_payments),
            SummaryItem("paying_users", "Платників", data.paying_users),
            SummaryItem("active_premium", "Активних Premium зараз", data.active_premium),
            SummaryItem("conversion", "Конверсія free → premium, %", percent(data.paying_users, data.registered_users)),
        )

    def sections(self, data: RevenueData, period: Period) -> tuple[ReportSection, ...]:
        revenue = ReportSection(
            key="revenue",
            title="Дохід за періодами",
            columns=(ReportColumn("bucket", "Період"), ReportColumn("revenue", "Дохід, грн"),
                     ReportColumn("payments", "Успішні платежі")),
            rows=[{"bucket": p.bucket, "revenue": p.revenue, "payments": p.payments} for p in data.points],
        )
        statuses = ReportSection(
            key="statuses",
            title="Платежі за статусами",
            columns=(ReportColumn("status", "Статус"), ReportColumn("count", "Кількість")),
            rows=[{"status": status, "count": count} for status, count in data.statuses],
        )
        return revenue, statuses


class ReportSettingsProvider(Protocol):
    def report_timezone(self) -> str: ...


class ReportsSource(PopularTitlesSource, UserActivitySource, RevenueSource, Protocol):
    def today(self, timezone: str) -> date: ...


def default_report_generators(source: ReportsSource) -> list[ReportGenerator[Any, Any]]:
    return [
        PopularTitlesReport(source, source.today),
        UserActivityReport(source, source.today),
        SubscriptionRevenueReport(source, source.today),
    ]


class ReportService:
    def __init__(self, generators: Iterable[ReportGenerator[Any, Any]], settings: ReportSettingsProvider) -> None:
        self.generators = {generator.kind: generator for generator in generators}
        self.settings = settings

    def kinds(self) -> tuple[str, ...]:
        return tuple(self.generators)

    def generate(self, kind: str, params: ReportParams) -> Report:
        generator = self.generators.get(kind)
        if generator is None:
            raise NotFoundError(
                f"Unknown report '{kind}'; expected one of: {', '.join(self.generators)}", code="unknown_report"
            )
        return generator.generate(replace(params, timezone=self.settings.report_timezone()))
