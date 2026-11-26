from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.models import TitleKind
from app.seed import seed_demo_catalog
from tests.factories import add_season, make_genre, make_title
from tests.helpers import assert_error


@pytest.fixture
def catalog() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        drama, comedy, scifi = (make_genre(session, n) for n in ("Drama", "comedy", "Sci-Fi"))
        matrix = make_title(session, "The Matrix", [scifi], year=1999, rating=8.7, description="A hacker")
        amelie = make_title(session, "Amelie", [comedy, drama], year=2001, country="France", rating=8.3)
        dark = make_title(
            session,
            "Dark",
            [scifi, drama],
            kind=TitleKind.SERIES.value,
            year=2017,
            country="Germany",
            rating=8.7,
            description="Time travel mystery",
        )
        make_title(session, "Taxi", [comedy], year=1998, country="France", rating=7.0)
        add_season(session, dark, 2, ["Ghosts", "Sic Mundus"])
        add_season(session, dark, 1, ["Secrets", "Lies", "Past and Present"])
        return {
            "drama": drama.id,
            "comedy": comedy.id,
            "scifi": scifi.id,
            "matrix": matrix.id,
            "amelie": amelie.id,
            "dark": dark.id,
        }


def search(client: TestClient, **params: Any) -> dict[str, Any]:
    r = client.get("/api/titles", params=params)
    assert r.status_code == 200, r.text
    return r.json()


def names(body: dict[str, Any]) -> list[str]:
    return [t["name"] for t in body["items"]]


def test_empty_catalog(client: TestClient) -> None:
    assert search(client) == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_titles_default_to_rating_desc_with_full_item_shape(client: TestClient, catalog: dict[str, int]) -> None:
    body = search(client)

    assert names(body) == ["The Matrix", "Dark", "Amelie", "Taxi"]
    assert body["total"] == 4
    assert body["items"][0] == {
        "id": catalog["matrix"],
        "kind": "movie",
        "name": "The Matrix",
        "description": "A hacker",
        "year": 1999,
        "country": "USA",
        "rating": 8.7,
        "poster_url": None,
        "genres": [{"id": catalog["scifi"], "name": "Sci-Fi"}],
        "is_favorite": False,
    }
    assert "seasons" not in body["items"][0]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"q": "TRAVEL"}, ["Dark"]),
        ({"country": "france"}, ["Amelie", "Taxi"]),
        ({"kind": "series"}, ["Dark"]),
        ({"year_from": 2000}, ["Dark", "Amelie"]),
        ({"year_to": 2000}, ["The Matrix", "Taxi"]),
        ({"min_rating": 8.5}, ["The Matrix", "Dark"]),
        ({"sort": "name"}, ["Amelie", "Dark", "Taxi", "The Matrix"]),
        ({"sort": "year", "order": "asc"}, ["Taxi", "The Matrix", "Amelie", "Dark"]),
        ({"sort": "popularity"}, ["The Matrix", "Amelie", "Dark", "Taxi"]),
    ],
)
def test_titles_filters(
    client: TestClient, catalog: dict[str, int], params: dict[str, Any], expected: list[str]
) -> None:
    body = search(client, **params)

    assert names(body) == expected
    assert body["total"] == len(expected)


def test_titles_filter_by_several_genres(client: TestClient, catalog: dict[str, int]) -> None:
    body = search(client, genre=[catalog["comedy"], catalog["scifi"]], sort="name")

    assert names(body) == ["Amelie", "Dark", "Taxi", "The Matrix"]


def test_titles_combined_filters(client: TestClient, catalog: dict[str, int]) -> None:
    body = search(client, genre=catalog["drama"], min_rating=8.5, kind="series", q="dark")

    assert names(body) == ["Dark"]


def test_titles_pagination(client: TestClient, catalog: dict[str, int]) -> None:
    body = search(client, sort="name", page=2, page_size=3)

    assert names(body) == ["The Matrix"]
    assert (body["total"], body["page"], body["page_size"]) == (4, 2, 3)


@pytest.mark.parametrize(
    "params",
    [
        {"page_size": 51},
        {"page_size": 0},
        {"page": 0},
        {"year_from": 2010, "year_to": 2000},
        {"kind": "cartoon"},
        {"sort": "price"},
        {"order": "up"},
        {"min_rating": 11},
        {"genre": "drama"},
        {"unknown": "x"},
    ],
)
def test_titles_rejects_invalid_params(client: TestClient, params: dict[str, Any]) -> None:
    assert_error(client.get("/api/titles", params=params), 422, "validation_error")


def test_title_detail_includes_genres_and_ordered_seasons(client: TestClient, catalog: dict[str, int]) -> None:
    r = client.get(f"/api/titles/{catalog['dark']}")

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Dark"
    assert [g["name"] for g in body["genres"]] == ["Drama", "Sci-Fi"]
    assert [s["number"] for s in body["seasons"]] == [1, 2]
    assert [(e["number"], e["name"]) for e in body["seasons"][0]["episodes"]] == [
        (1, "Secrets"),
        (2, "Lies"),
        (3, "Past and Present"),
    ]
    assert [e["name"] for e in body["seasons"][1]["episodes"]] == ["Ghosts", "Sic Mundus"]


def test_movie_detail_has_no_seasons(client: TestClient, catalog: dict[str, int]) -> None:
    assert client.get(f"/api/titles/{catalog['matrix']}").json()["seasons"] == []


def test_title_detail_not_found(client: TestClient) -> None:
    assert_error(client.get("/api/titles/999999"), 404, "title_not_found")


def test_genres_sorted_case_insensitively(client: TestClient, catalog: dict[str, int]) -> None:
    r = client.get("/api/genres")

    assert r.status_code == 200
    assert r.json() == [
        {"id": catalog["comedy"], "name": "comedy"},
        {"id": catalog["drama"], "name": "Drama"},
        {"id": catalog["scifi"], "name": "Sci-Fi"},
    ]


def test_countries_are_unique_and_sorted(client: TestClient, catalog: dict[str, int]) -> None:
    r = client.get("/api/countries")

    assert r.status_code == 200
    assert r.json() == ["France", "Germany", "USA"]


def test_search_on_demo_catalog_handles_cyrillic(client: TestClient) -> None:
    with SessionLocal() as session, session.begin():
        seed_demo_catalog(session)

    assert names(search(client, q="ТЕМНИЙ")) == ["Темний лицар"]
    assert names(search(client, q="подорожі в ЧАСІ")) == ["Темрява"]
    assert names(search(client, country="україна", kind="series")) == ["Слуга народу"]
    assert search(client, page_size=50)["total"] == 31
