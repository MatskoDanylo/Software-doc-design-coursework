from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from tests.factories import make_title, make_user
from tests.helpers import assert_error

PERIOD = {"date_from": "2026-11-10", "date_to": "2026-11-11"}


@pytest.fixture
def late_signup(seeded: None) -> None:
    with SessionLocal() as session, session.begin():
        make_user(session, "late@example.com", created_at=datetime(2026, 11, 10, 23, 30, tzinfo=UTC))
        make_title(session, "Heat")


def report(client: TestClient, headers: dict[str, str], kind: str, **params: Any) -> dict[str, Any]:
    r = client.get(f"/api/admin/reports/{kind}", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def registrations(body: dict[str, Any]) -> dict[str, int]:
    [activity] = body["sections"]
    return {row["bucket"]: row["registrations"] for row in activity["rows"]}


def test_json_report_uses_timezone_from_settings(
    client: TestClient, admin_headers: dict[str, str], late_signup: None
) -> None:
    body = report(client, admin_headers, "user-activity", **PERIOD)

    assert (body["kind"], body["title"], body["timezone"]) == ("user-activity", "Активність користувачів", "Europe/Kyiv")
    assert (body["date_from"], body["date_to"], body["group_by"]) == ("2026-11-10", "2026-11-11", "day")
    assert registrations(body) == {"2026-11-10": 0, "2026-11-11": 1}
    assert body["summary"][0] == {"key": "new_users", "label": "Нових користувачів", "value": 1}
    assert body["sections"][0]["columns"][0] == {"key": "bucket", "label": "Період"}

    settings = client.get("/api/admin/settings", headers=admin_headers).json()
    update = {k: settings[k] for k in ("recommendation_default_strategy", "hybrid_weights", "popularity_window_days")}
    assert client.put("/api/admin/settings", json=update | {"report_timezone": "UTC"},
                      headers=admin_headers).status_code == 200

    body = report(client, admin_headers, "user-activity", **PERIOD)
    assert body["timezone"] == "UTC"
    assert registrations(body) == {"2026-11-10": 1, "2026-11-11": 0}


@pytest.mark.parametrize("kind", ["popular-titles", "user-activity", "subscription-revenue"])
def test_every_report_has_defaults(client: TestClient, admin_headers: dict[str, str], kind: str) -> None:
    body = report(client, admin_headers, kind)

    assert body["kind"] == kind
    assert body["date_from"] < body["date_to"]
    assert body["sections"] and body["summary"]


def test_monthly_grouping_via_query(client: TestClient, admin_headers: dict[str, str], late_signup: None) -> None:
    body = report(client, admin_headers, "user-activity", date_from="2026-10-01", date_to="2026-11-30",
                  group_by="month")

    assert registrations(body) == {"2026-10-01": 0, "2026-11-01": 1}


def test_csv_export(client: TestClient, admin_headers: dict[str, str], late_signup: None) -> None:
    r = client.get("/api/admin/reports/subscription-revenue", headers=admin_headers,
                   params={"date_from": "2026-11-01", "date_to": "2026-11-30", "format": "csv"})

    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"] == (
        'attachment; filename="subscription-revenue_2026-11-01_2026-11-30.csv"'
    )
    assert r.content.startswith(b"\xef\xbb\xbf")
    lines = r.content.decode("utf-8-sig").split("\r\n")
    assert lines[0] == "Доходи від підписок"
    assert "Конверсія free → premium, %;0" in lines
    assert "Період;Дохід, грн;Успішні платежі" in lines
    assert "2026-11-01;0;0" in lines
    assert "Статус;Кількість" in lines


@pytest.mark.parametrize(("path", "params", "status", "code"), [
    ("/api/admin/reports/cohorts", {}, 404, "unknown_report"),
    ("/api/admin/reports/user-activity", {"date_from": "2026-11-02", "date_to": "2026-11-01"}, 422, "invalid_period"),
    ("/api/admin/reports/user-activity", {"date_from": "2024-01-01", "date_to": "2026-01-01"}, 422, "period_too_long"),
    ("/api/admin/reports/user-activity", {"group_by": "week"}, 422, "validation_error"),
    ("/api/admin/reports/user-activity", {"format": "xml"}, 422, "validation_error"),
    ("/api/admin/reports/user-activity", {"date_from": "yesterday"}, 422, "validation_error"),
])
def test_report_errors(
    client: TestClient, admin_headers: dict[str, str], path: str, params: dict[str, str], status: int, code: str
) -> None:
    assert_error(client.get(path, params=params, headers=admin_headers), status, code)


@pytest.mark.parametrize("path", ["/api/admin/reports/user-activity", "/api/admin/dashboard"])
def test_reports_require_admin(client: TestClient, user_headers: dict[str, str], path: str) -> None:
    assert_error(client.get(path), 401, "unauthorized")
    assert_error(client.get(path, headers=user_headers), 403, "forbidden")


def test_dashboard(client: TestClient, admin_headers: dict[str, str], late_signup: None) -> None:
    r = client.get("/api/admin/dashboard", headers=admin_headers)

    assert r.status_code == 200, r.text
    assert r.json() == {
        "total_users": 1, "active_users_7d": 0, "active_premium": 0, "revenue_30d": 0.0, "titles_with_video": 0,
    }
