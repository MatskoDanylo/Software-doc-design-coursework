from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.models import Favorite, Title
from app.repositories.title_stats_repository import TitleStatsRepository
from app.repositories.users import UserRepository
from tests.factories import add_history, make_genre, make_title, make_user
from tests.helpers import assert_error

RECENT = datetime.now(UTC) - timedelta(days=1)
LONG_AGO = datetime.now(UTC) - timedelta(days=30)


@pytest.fixture
def catalog() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        drama, comedy, scifi = (make_genre(session, n) for n in ("Драма", "Комедія", "Фантастика"))
        titles = {
            "d1": make_title(session, "Drama One", [drama], year=2010, country="США", rating=7.0),
            "d2": make_title(session, "Drama Two", [drama], year=2012, country="США", rating=8.0),
            "d3": make_title(session, "Drama Three", [drama], year=1990, country="Франція", rating=6.0),
            "c1": make_title(session, "Comedy One", [comedy], year=2015, country="Італія", rating=9.0),
            "s1": make_title(session, "Space", [scifi], year=2020, country="Японія", rating=8.5),
        }
        viewers = [make_user(session, f"viewer{i}@example.com") for i in range(3)]
        for viewer in viewers:
            add_history(session, viewer.id, titles["c1"], last_watched=RECENT)
        add_history(session, viewers[0].id, titles["s1"], last_watched=RECENT)
        for viewer in viewers[:2]:
            add_history(session, viewer.id, titles["d3"], finished=True, last_watched=LONG_AGO)
        TitleStatsRepository(session).rebuild()
        return {key: t.id for key, t in titles.items()}


def user_id(email: str = "user@example.com") -> int:
    with SessionLocal() as session:
        user = UserRepository(session).get_by_email(email)
        assert user is not None
        return user.id


def watch(email: str, title_id: int, finished: bool = True) -> None:
    with SessionLocal() as session, session.begin():
        title = session.get_one(Title, title_id)
        add_history(session, user_id(email), title, finished=finished, last_watched=RECENT)


def favorite(email: str, title_id: int) -> None:
    with SessionLocal() as session, session.begin():
        session.add(Favorite(user_id=user_id(email), title_id=title_id))


def recommendations(client: TestClient, headers: dict[str, str] | None = None, **params: Any) -> dict[str, Any]:
    r = client.get("/api/recommendations", params=params, headers=headers or {})
    assert r.status_code == 200, r.text
    return r.json()


def ids(items: list[dict[str, Any]]) -> list[int]:
    return [item["id"] for item in items]


def test_guest_gets_popular_titles_with_tiered_reasons(client: TestClient, catalog: dict[str, int]) -> None:
    body = recommendations(client)

    assert body["strategy"] == "popularity"
    assert ids(body["items"]) == [catalog[k] for k in ("c1", "s1", "d3", "d2", "d1")]
    assert [i["reason"] for i in body["items"]] == [
        "Популярне цього тижня", "Популярне цього тижня", "Популярне серед глядачів", "Високий рейтинг",
        "Високий рейтинг",
    ]
    assert body["items"][0]["genres"][0]["name"] == "Комедія"
    assert all(i["is_favorite"] is False for i in body["items"])


def test_guest_cannot_switch_to_personal_strategy(client: TestClient, catalog: dict[str, int]) -> None:
    assert recommendations(client, strategy="genre_affinity", limit=2)["strategy"] == "popularity"


def test_unknown_strategy_is_rejected(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    assert_error(client.get("/api/recommendations", params={"strategy": "random"}), 422, "unknown_strategy")
    assert_error(
        client.get("/api/recommendations", params={"strategy": "random"}, headers=user_headers),
        422, "unknown_strategy",
    )


@pytest.mark.parametrize("limit", [0, 51])
def test_limit_is_validated(client: TestClient, limit: int) -> None:
    assert_error(client.get("/api/recommendations", params={"limit": limit}), 422, "validation_error")


def test_cold_start_user_gets_popularity(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    body = recommendations(client, user_headers, strategy="genre_affinity", limit=3)

    assert body["strategy"] == "popularity"
    assert ids(body["items"]) == [catalog["c1"], catalog["s1"], catalog["d3"]]


def test_personal_hybrid_excludes_watched_and_explains_choice(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    watch("user@example.com", catalog["d1"])

    body = recommendations(client, user_headers, limit=5)

    assert body["strategy"] == "hybrid"
    assert catalog["d1"] not in ids(body["items"])
    assert set(ids(body["items"])) == {catalog[k] for k in ("d2", "d3", "c1", "s1")}
    first = body["items"][0]
    assert first["id"] == catalog["d2"]
    assert first["reason"] in {"Бо ви дивились жанр «Драма»", "Схоже на «Drama One»"}
    scores = [i["score"] for i in body["items"]]
    assert scores == sorted(scores, reverse=True)


def test_genre_affinity_is_filled_up_to_limit_with_popular_titles(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    watch("user@example.com", catalog["d1"])

    body = recommendations(client, user_headers, strategy="genre_affinity", limit=4)

    assert body["strategy"] == "genre_affinity"
    assert ids(body["items"]) == [catalog[k] for k in ("d2", "d3", "c1", "s1")]
    assert [i["reason"] for i in body["items"]] == [
        "Бо ви дивились жанр «Драма»", "Бо ви дивились жанр «Драма»",
        "Популярне цього тижня", "Популярне цього тижня",
    ]
    scores = [i["score"] for i in body["items"]]
    assert scores == sorted(scores, reverse=True)


def test_favorites_drive_affinity_but_are_not_recommended(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    favorite("user@example.com", catalog["d1"])

    body = recommendations(client, user_headers, strategy="genre_affinity", limit=2)

    assert ids(body["items"]) == [catalog["d2"], catalog["d3"]]
    assert body["items"][0]["reason"] == "Бо у вашому Вибраному є жанр «Драма»"


def test_similar_titles_for_guest(client: TestClient, catalog: dict[str, int]) -> None:
    r = client.get(f"/api/titles/{catalog['d1']}/similar")

    assert r.status_code == 200, r.text
    items = r.json()
    assert ids(items)[:2] == [catalog["d2"], catalog["d3"]]
    assert catalog["d1"] not in ids(items)
    assert {i["reason"] for i in items} == {"Схоже на «Drama One»"}


def test_similar_titles_skip_watched_and_mark_favorites(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    watch("user@example.com", catalog["d2"], finished=False)
    favorite("user@example.com", catalog["d3"])

    r = client.get(f"/api/titles/{catalog['d1']}/similar", params={"limit": 1}, headers=user_headers)

    assert r.status_code == 200, r.text
    [item] = r.json()
    assert (item["id"], item["is_favorite"]) == (catalog["d3"], True)


def test_similar_for_missing_title_is_not_found(client: TestClient) -> None:
    assert_error(client.get("/api/titles/999/similar"), 404, "title_not_found")
