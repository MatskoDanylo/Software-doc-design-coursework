from datetime import date
from typing import Any

import pytest

from app.core.errors import NotFoundError, UnprocessableError
from app.services.report_export import CsvReportExporter
from app.services.reports import (
    GroupBy,
    Period,
    Report,
    ReportColumn,
    ReportGenerator,
    ReportParams,
    ReportSection,
    ReportService,
    SubscriptionRevenueReport,
    SummaryItem,
    UserActivityReport,
    fill_buckets,
)

TODAY = date(2026, 11, 25)


class RecordingReport(ReportGenerator[list[int], int]):
    kind = "recording"
    title = "Тестовий звіт"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.timezones: list[str] = []
        super().__init__(self._today)

    def _today(self, timezone: str) -> date:
        self.timezones.append(timezone)
        return TODAY

    def collect(self, period: Period) -> list[int]:
        self.calls.append("collect")
        return [1, 2, 3]

    def aggregate(self, rows: list[int], period: Period) -> int:
        self.calls.append("aggregate")
        return sum(rows)

    def summarize(self, data: int, period: Period) -> tuple[SummaryItem, ...]:
        self.calls.append("summarize")
        return (SummaryItem("total", "Разом", data),)

    def sections(self, data: int, period: Period) -> tuple[ReportSection, ...]:
        self.calls.append("sections")
        return (ReportSection("main", "Дані", (ReportColumn("value", "Значення"),), [{"value": data}]),)


class MonthlyQuarterReport(RecordingReport):
    kind = "monthly"

    def default_period(self, today: date) -> tuple[date, date]:
        return date(today.year, 1, 1), today

    def default_group_by(self) -> GroupBy:
        return GroupBy.MONTH

    def extra_validation(self, period: Period) -> None:
        if period.date_to.year != period.date_from.year:
            raise UnprocessableError("Report must stay within one year", code="cross_year")


def test_template_method_runs_steps_in_order() -> None:
    generator = RecordingReport()

    report = generator.generate(ReportParams(timezone="Europe/Kyiv"))

    assert generator.calls == ["collect", "aggregate", "summarize", "sections"]
    assert generator.timezones == ["Europe/Kyiv"]
    assert report == Report(
        kind="recording",
        title="Тестовий звіт",
        date_from=date(2026, 10, 27),
        date_to=TODAY,
        group_by=GroupBy.DAY,
        timezone="Europe/Kyiv",
        summary=(SummaryItem("total", "Разом", 6),),
        sections=(ReportSection("main", "Дані", (ReportColumn("value", "Значення"),), [{"value": 6}]),),
    )


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        (ReportParams(date_to=date(2026, 6, 30)), (date(2026, 6, 1), date(2026, 6, 30))),
        (ReportParams(date_from=date(2026, 11, 1)), (date(2026, 11, 1), TODAY)),
        (ReportParams(date_from=date(2026, 1, 5), date_to=date(2026, 1, 5)), (date(2026, 1, 5), date(2026, 1, 5))),
    ],
)
def test_missing_dates_are_filled_from_the_default_period(params: ReportParams, expected: tuple[date, date]) -> None:
    report = RecordingReport().generate(params)

    assert (report.date_from, report.date_to) == expected


def test_reversed_period_is_rejected_before_collecting() -> None:
    generator = RecordingReport()

    with pytest.raises(UnprocessableError) as error:
        generator.generate(ReportParams(date_from=date(2026, 11, 2), date_to=date(2026, 11, 1)))

    assert (error.value.status_code, error.value.code) == (422, "invalid_period")
    assert generator.calls == []


def test_overly_long_period_is_rejected() -> None:
    with pytest.raises(UnprocessableError) as error:
        RecordingReport().generate(ReportParams(date_from=date(2000, 1, 1), date_to=date(2026, 1, 1)))

    assert error.value.code == "period_too_long"


def test_hooks_can_be_overridden_by_subclasses() -> None:
    generator = MonthlyQuarterReport()

    report = generator.generate(ReportParams())

    assert (report.date_from, report.date_to, report.group_by) == (date(2026, 1, 1), TODAY, GroupBy.MONTH)
    with pytest.raises(UnprocessableError) as error:
        generator.generate(ReportParams(date_from=date(2025, 12, 1), date_to=date(2026, 1, 31)))
    assert error.value.code == "cross_year"


def test_explicit_group_by_wins_over_the_hook() -> None:
    assert MonthlyQuarterReport().generate(ReportParams(group_by=GroupBy.DAY)).group_by is GroupBy.DAY


def test_template_method_cannot_be_overridden() -> None:
    with pytest.raises(TypeError, match="must not override the template method"):

        class Rogue(RecordingReport):
            def generate(self, params: ReportParams) -> Report:  # type: ignore[misc]
                raise AssertionError


def test_concrete_reports_customize_hooks() -> None:
    revenue = SubscriptionRevenueReport(source=None, today=lambda tz: TODAY)  # type: ignore[arg-type]
    activity = UserActivityReport(source=None, today=lambda tz: TODAY)  # type: ignore[arg-type]

    assert revenue.default_period(TODAY) == (date(2026, 8, 28), TODAY)
    assert activity.default_period(TODAY) == (date(2026, 10, 27), TODAY)
    with pytest.raises(UnprocessableError) as error:
        activity.validate(ReportParams(date_from=date(2025, 1, 1), date_to=date(2026, 1, 2)))
    assert error.value.code == "period_too_long"
    monthly = activity.validate(
        ReportParams(date_from=date(2025, 1, 1), date_to=date(2026, 1, 2), group_by=GroupBy.MONTH)
    )
    assert monthly.days == 367


def test_fill_buckets_by_day_and_month() -> None:
    days = fill_buckets(Period(date(2026, 2, 27), date(2026, 3, 2), GroupBy.DAY, "UTC"))
    months = fill_buckets(Period(date(2025, 11, 15), date(2026, 2, 3), GroupBy.MONTH, "UTC"))

    assert days == [date(2026, 2, 27), date(2026, 2, 28), date(2026, 3, 1), date(2026, 3, 2)]
    assert months == [date(2025, 11, 1), date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)]


class FixedTimezone:
    def report_timezone(self) -> str:
        return "Europe/Kyiv"


def test_report_service_dispatches_by_kind_with_configured_timezone() -> None:
    generator = RecordingReport()
    service = ReportService([generator], FixedTimezone())

    report = service.generate("recording", ReportParams(timezone="ignored"))

    assert report.timezone == "Europe/Kyiv"
    assert service.kinds() == ("recording",)
    with pytest.raises(NotFoundError) as error:
        service.generate("nope", ReportParams())
    assert (error.value.status_code, error.value.code) == (404, "unknown_report")


def sample_report() -> Report:
    return Report(
        kind="sample",
        title="Доходи",
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 2),
        group_by=GroupBy.DAY,
        timezone="Europe/Kyiv",
        summary=(SummaryItem("total", "Дохід, грн", 198.5), SummaryItem("top", "Найкращий", None)),
        sections=(
            ReportSection(
                "rows",
                "Дохід за днями",
                (ReportColumn("bucket", "Період"), ReportColumn("sum", "Сума")),
                [{"bucket": date(2026, 11, 1), "sum": 99.0}, {"bucket": date(2026, 11, 2), "sum": 99.5}],
            ),
            ReportSection("names", "Тайтли", (ReportColumn("name", "Назва"),), [{"name": "Кіно; частина 2"}]),
        ),
    )


def test_csv_export_has_bom_semicolons_and_cyrillic() -> None:
    exporter = CsvReportExporter()

    content = exporter.export(sample_report())

    assert content.startswith(b"\xef\xbb\xbf")
    lines = content.decode("utf-8-sig").split("\r\n")
    assert lines[:9] == [
        "Доходи",
        "Період;2026-11-01 — 2026-11-02",
        "Групування;по днях",
        "Часовий пояс;Europe/Kyiv",
        "",
        "Підсумок",
        "Дохід, грн;198,5",
        "Найкращий;",
        "",
    ]
    assert lines[9:16] == [
        "Дохід за днями",
        "Період;Сума",
        "2026-11-01;99",
        "2026-11-02;99,5",
        "",
        "Тайтли",
        "Назва",
    ]
    assert lines[16] == '"Кіно; частина 2"'
    assert exporter.filename(sample_report()) == "sample_2026-11-01_2026-11-02.csv"


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (None, ""),
        (3, "3"),
        (0.25, "0,25"),
        (123456.75, "123456,75"),
        (1980.0, "1980"),
        (date(2026, 1, 2), "2026-01-02"),
        ("Драма", "Драма"),
    ],
)
def test_csv_value_formatting(value: Any, text: str) -> None:
    assert CsvReportExporter.format(value) == text
