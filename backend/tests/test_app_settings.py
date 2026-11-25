from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import AppSetting
from app.patterns.recommendation import RecommendationConfig, default_strategy_registry
from app.repositories.settings_repository import SettingsRepository
from app.repositories.title_stats_repository import TitleStatsRepository
from app.repositories.users import UserRepository
from app.schemas.settings import AppSettingsRead
from app.services.settings_service import SettingsService
from tests.factories import add_history, make_genre, make_title, make_user
from tests.helpers import assert_error

VALID: dict[str, Any] = {
    "recommendation_default_strategy": "genre_affinity",
    "hybrid_weights": {"genre_affinity": 0.7, "popularity": 0.3, "similar": 0.0},
    "popularity_window_days": 30,
    "report_timezone": "UTC",
}
DEFAULTS: dict[str, Any] = {
    "recommendation_default_strategy": "hybrid",
    "hybrid_weights": {"genre_affinity": 0.5, "similar": 0.3, "popularity": 0.2},
    "popularity_window_days": 7,
    "report_timezone": "Europe/Kyiv",
}


def put(client: TestClient, headers: dict[str, str], **changes: Any) -> Any:
    return client.put("/api/admin/settings", json=VALID | changes, headers=headers)


def read_settings() -> AppSettingsRead:
    with SessionLocal() as session:
        return SettingsService(SettingsRepository(session), default_strategy_registry().codes()).get()


def read_configs() -> tuple[RecommendationConfig, str]:
    with SessionLocal() as session:
        settings = SettingsService(SettingsRepository(session), default_strategy_registry().codes())
        return settings.recommendation_config(), settings.report_timezone()


def test_defaults_are_returned_without_stored_rows(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = client.get("/api/admin/settings", headers=admin_headers)

    assert r.status_code == 200, r.text
    body = r.json()
    assert {k: body[k] for k in DEFAULTS} == DEFAULTS
    assert body["available_strategies"] == ["popularity", "genre_affinity", "similar", "hybrid"]
    assert body["updated_at"] is None


def test_update_is_persisted(client: TestClient, admin_headers: dict[str, str]) -> None:
    r = put(client, admin_headers)

    assert r.status_code == 200, r.text
    assert {k: r.json()[k] for k in VALID} == VALID
    assert r.json()["updated_at"] is not None
    again = client.get("/api/admin/settings", headers=admin_headers).json()
    assert {k: again[k] for k in VALID} == VALID
    with SessionLocal() as session:
        assert {s.key: s.value for s in session.scalars(select(AppSetting))} == VALID


def test_second_update_overwrites_values(client: TestClient, admin_headers: dict[str, str]) -> None:
    put(client, admin_headers)

    r = put(client, admin_headers, popularity_window_days=90, report_timezone="Europe/Kyiv")

    assert (r.json()["popularity_window_days"], r.json()["report_timezone"]) == (90, "Europe/Kyiv")


@pytest.mark.parametrize(("changes", "code"), [
    ({"recommendation_default_strategy": "random"}, "unknown_strategy"),
    ({"hybrid_weights": {"genre_affinity": 0.5, "telepathy": 0.5}}, "unknown_strategy"),
    ({"hybrid_weights": {"hybrid": 0.5}}, "unknown_strategy"),
    ({"hybrid_weights": {"popularity": 1.5}}, "validation_error"),
    ({"hybrid_weights": {"popularity": -0.1}}, "validation_error"),
    ({"hybrid_weights": {"popularity": 0.0, "similar": 0.0}}, "validation_error"),
    ({"hybrid_weights": {}}, "validation_error"),
    ({"popularity_window_days": 0}, "validation_error"),
    ({"popularity_window_days": 366}, "validation_error"),
    ({"report_timezone": "Mars/Olympus_Mons"}, "unknown_timezone"),
    ({"report_timezone": "europe/kyiv"}, "unknown_timezone"),
    ({"theme": "dark"}, "validation_error"),
])
def test_invalid_settings_are_rejected(
    client: TestClient, admin_headers: dict[str, str], changes: dict[str, Any], code: str
) -> None:
    assert_error(put(client, admin_headers, **changes), 422, code)
    assert client.get("/api/admin/settings", headers=admin_headers).json()["updated_at"] is None


def test_put_requires_all_fields(client: TestClient, admin_headers: dict[str, str]) -> None:
    partial = {"popularity_window_days": 14}

    assert_error(client.put("/api/admin/settings", json=partial, headers=admin_headers), 422, "validation_error")


@pytest.mark.parametrize("window_days", [1, 365])
def test_window_bounds_are_accepted(client: TestClient, admin_headers: dict[str, str], window_days: int) -> None:
    assert put(client, admin_headers, popularity_window_days=window_days).status_code == 200


def test_settings_require_admin(client: TestClient, user_headers: dict[str, str]) -> None:
    assert_error(client.get("/api/admin/settings"), 401, "unauthorized")
    assert_error(client.get("/api/admin/settings", headers=user_headers), 403, "forbidden")
    assert_error(put(client, user_headers), 403, "forbidden")


def test_invalid_stored_values_fall_back_to_defaults() -> None:
    with SessionLocal() as session, session.begin():
        session.add_all([
            AppSetting(key="recommendation_default_strategy", value="removed_strategy"),
            AppSetting(key="popularity_window_days", value="often"),
            AppSetting(key="hybrid_weights", value={"popularity": 1.0}),
        ])

    settings = read_settings()

    assert settings.recommendation_default_strategy == "hybrid"
    assert settings.popularity_window_days == 7
    assert settings.hybrid_weights == {"popularity": 1.0}


def test_service_exposes_typed_configs(client: TestClient, admin_headers: dict[str, str]) -> None:
    put(client, admin_headers)

    assert read_configs() == (
        RecommendationConfig(
            default_strategy="genre_affinity",
            hybrid_weights={"genre_affinity": 0.7, "popularity": 0.3, "similar": 0.0},
            popularity_window_days=30,
        ),
        "UTC",
    )


@pytest.fixture
def watched_catalog(user_headers: dict[str, str]) -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        drama, comedy = make_genre(session, "Драма"), make_genre(session, "Комедія")
        seen = make_title(session, "Seen", [drama], country="США")
        other_drama = make_title(session, "Other Drama", [drama], country="Франція")
        old_hit = make_title(session, "Old Hit", [comedy], country="Італія")
        viewer = make_user(session, "viewer@example.com")
        add_history(session, viewer.id, old_hit, finished=True, last_watched=datetime.now(UTC) - timedelta(days=10))
        user = UserRepository(session).get_by_email("user@example.com")
        assert user is not None
        add_history(session, user.id, seen, finished=True)
        TitleStatsRepository(session).rebuild()
        return {"seen": seen.id, "other_drama": other_drama.id, "old_hit": old_hit.id}


def reasons(client: TestClient, headers: dict[str, str], **params: Any) -> tuple[str, dict[int, str]]:
    body = client.get("/api/recommendations", params=params, headers=headers).json()
    return body["strategy"], {i["id"]: i["reason"] for i in body["items"]}


def test_settings_drive_the_recommendation_service(
    client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str], watched_catalog: dict[str, int]
) -> None:
    strategy, by_id = reasons(client, user_headers)
    assert strategy == "hybrid"
    assert by_id[watched_catalog["old_hit"]] == "Популярне серед глядачів"

    put(client, admin_headers, recommendation_default_strategy="popularity", popularity_window_days=14)

    strategy, by_id = reasons(client, user_headers)
    assert strategy == "popularity"
    assert by_id[watched_catalog["old_hit"]] == "Популярне за останні 14 днів"


def test_hybrid_weights_from_settings_change_the_mix(
    client: TestClient, admin_headers: dict[str, str], user_headers: dict[str, str], watched_catalog: dict[str, int]
) -> None:
    put(client, admin_headers, recommendation_default_strategy="hybrid",
        hybrid_weights={"popularity": 1.0, "genre_affinity": 0.0, "similar": 0.0})

    _, by_id = reasons(client, user_headers)

    assert by_id[watched_catalog["other_drama"]] == "Високий рейтинг"
    assert watched_catalog["seen"] not in by_id
