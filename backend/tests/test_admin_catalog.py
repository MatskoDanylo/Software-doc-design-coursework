from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.db import SessionLocal
from app.models import Episode, Genre, Season, Title, TitleKind, title_genres
from app.services.poster_service import MAX_POSTER_BYTES
from tests.factories import add_season, make_genre, make_title
from tests.helpers import assert_error

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64

ENDPOINTS: list[tuple[str, str, dict[str, Any]]] = [
    ("POST", "/api/admin/titles", {"json": {"kind": "movie", "name": "X", "year": 2000, "country": "USA"}}),
    ("PATCH", "/api/admin/titles/1", {"json": {"rating": 5}}),
    ("DELETE", "/api/admin/titles/1", {}),
    ("POST", "/api/admin/titles/1/poster", {"files": {"file": ("p.png", PNG, "image/png")}}),
    ("POST", "/api/admin/genres", {"json": {"name": "Drama"}}),
    ("PATCH", "/api/admin/genres/1", {"json": {"name": "Drama"}}),
    ("DELETE", "/api/admin/genres/1", {}),
    ("POST", "/api/admin/titles/1/seasons", {"json": {"number": 1}}),
    ("PATCH", "/api/admin/seasons/1", {"json": {"number": 2}}),
    ("DELETE", "/api/admin/seasons/1", {}),
    ("POST", "/api/admin/seasons/1/episodes", {"json": {"number": 1, "name": "Pilot"}}),
    ("PATCH", "/api/admin/episodes/1", {"json": {"name": "Pilot"}}),
    ("DELETE", "/api/admin/episodes/1", {}),
]


@pytest.fixture
def ids() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        drama, comedy = make_genre(session, "Drama"), make_genre(session, "Comedy")
        movie = make_title(session, "Taxi", [comedy], year=1998, country="France")
        series = make_title(session, "Dark", [drama], kind=TitleKind.SERIES.value, year=2017, country="Germany")
        season = add_season(session, series, 1, ["Secrets", "Lies"])
        return {
            "drama": drama.id,
            "comedy": comedy.id,
            "movie": movie.id,
            "series": series.id,
            "season": season.id,
            "episode": season.episodes[0].id,
        }


def count(model: Any) -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(model))


def poster_path(url: str) -> Path:
    return Path(settings.media_dir) / url.removeprefix("/media/")


@pytest.mark.parametrize(("method", "path", "kwargs"), ENDPOINTS)
def test_admin_catalog_requires_auth(client: TestClient, method: str, path: str, kwargs: dict[str, Any]) -> None:
    assert_error(client.request(method, path, **kwargs), 401, "unauthorized")


@pytest.mark.parametrize(("method", "path", "kwargs"), ENDPOINTS)
def test_admin_catalog_forbidden_for_user(
    client: TestClient, user_headers: dict[str, str], method: str, path: str, kwargs: dict[str, Any]
) -> None:
    assert_error(client.request(method, path, headers=user_headers, **kwargs), 403, "forbidden")


@pytest.mark.parametrize(("method", "path", "kwargs"), ENDPOINTS)
def test_admin_catalog_allowed_for_admin(
    client: TestClient, admin_headers: dict[str, str], method: str, path: str, kwargs: dict[str, Any]
) -> None:
    assert client.request(method, path, headers=admin_headers, **kwargs).status_code not in (401, 403)


class TestTitles:
    def test_create(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        payload = {
            "kind": "movie",
            "name": "  Amelie ",
            "description": "Paris",
            "year": 2001,
            "country": "France",
            "rating": 8.3,
            "genre_ids": [ids["drama"], ids["comedy"], ids["drama"]],
        }

        r = client.post("/api/admin/titles", headers=admin_headers, json=payload)

        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Amelie" and body["poster_url"] is None and body["seasons"] == []
        assert [g["name"] for g in body["genres"]] == ["Comedy", "Drama"]
        assert client.get(f"/api/titles/{body['id']}").json()["name"] == "Amelie"

    def test_create_defaults(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        payload = {"kind": "series", "name": "New", "year": 2024, "country": "Україна"}

        body = client.post("/api/admin/titles", headers=admin_headers, json=payload).json()

        assert (body["description"], body["rating"], body["genres"]) == ("", 0.0, [])

    @pytest.mark.parametrize(
        "override",
        [
            {"kind": "cartoon"},
            {"name": "   "},
            {"year": 1800},
            {"rating": 10.5},
            {"country": ""},
            {"genre_ids": ["x"]},
            {"poster_url": "/hack.png"},
            {"name": None},
        ],
    )
    def test_create_validates(self, client: TestClient, admin_headers: dict[str, str], override: dict) -> None:
        payload = {"kind": "movie", "name": "X", "year": 2000, "country": "USA"} | override

        assert_error(client.post("/api/admin/titles", headers=admin_headers, json=payload), 422, "validation_error")

    def test_create_rejects_unknown_genre(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        payload = {"kind": "movie", "name": "X", "year": 2000, "country": "USA", "genre_ids": [999]}

        assert_error(client.post("/api/admin/titles", headers=admin_headers, json=payload), 422, "unknown_genre")
        assert count(Title) == 0

    def test_create_rejects_duplicate(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        payload = {"kind": "movie", "name": "Taxi", "year": 1998, "country": "USA"}

        assert_error(client.post("/api/admin/titles", headers=admin_headers, json=payload), 409, "title_exists")
        remake = payload | {"year": 2004}
        assert client.post("/api/admin/titles", headers=admin_headers, json=remake).status_code == 201

    def test_update_is_partial(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.patch(
            f"/api/admin/titles/{ids['movie']}",
            headers=admin_headers,
            json={"rating": 7.5, "genre_ids": [ids["drama"]]},
        )

        assert r.status_code == 200
        body = r.json()
        assert (body["name"], body["year"], body["rating"]) == ("Taxi", 1998, 7.5)
        assert [g["name"] for g in body["genres"]] == ["Drama"]
        assert client.get(f"/api/titles/{ids['movie']}").json()["rating"] == 7.5

    def test_update_can_clear_genres(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        r = client.patch(f"/api/admin/titles/{ids['movie']}", headers=admin_headers, json={"genre_ids": []})

        assert r.json()["genres"] == []
        assert count(Genre) == 2

    @pytest.mark.parametrize("payload", [{"name": None}, {"rating": -1}, {"kind": None}, {"unknown": 1}])
    def test_update_validates(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int], payload: dict
    ) -> None:
        r = client.patch(f"/api/admin/titles/{ids['movie']}", headers=admin_headers, json=payload)

        assert_error(r, 422, "validation_error")

    def test_update_rejects_duplicate_identity(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        r = client.patch(
            f"/api/admin/titles/{ids['series']}", headers=admin_headers, json={"name": "Taxi", "year": 1998}
        )
        assert r.status_code == 200, "different kind is a different title"

        r = client.patch(
            f"/api/admin/titles/{ids['series']}", headers=admin_headers, json={"name": "Taxi", "year": 1998}
        )
        assert r.status_code == 200, "re-saving the same identity is not a conflict"

        with SessionLocal() as session, session.begin():
            make_title(session, "Taxi", kind=TitleKind.SERIES.value, year=2000)
        r = client.patch(f"/api/admin/titles/{ids['series']}", headers=admin_headers, json={"year": 2000})
        assert_error(r, 409, "title_exists")

    def test_series_with_seasons_cannot_become_movie(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        r = client.patch(f"/api/admin/titles/{ids['series']}", headers=admin_headers, json={"kind": "movie"})

        assert_error(r, 409, "title_has_seasons")

    def test_update_unknown_genre(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.patch(f"/api/admin/titles/{ids['movie']}", headers=admin_headers, json={"genre_ids": [999]})

        assert_error(r, 422, "unknown_genre")

    def test_delete_cascades(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.delete(f"/api/admin/titles/{ids['series']}", headers=admin_headers)

        assert r.status_code == 204 and r.content == b""
        assert_error(client.get(f"/api/titles/{ids['series']}"), 404, "title_not_found")
        assert (count(Title), count(Season), count(Episode), count(title_genres)) == (1, 0, 0, 1)
        assert count(Genre) == 2

    @pytest.mark.parametrize(
        ("method", "kwargs"), [("PATCH", {"json": {"rating": 1}}), ("DELETE", {}), ("POST", {"json": {"number": 1}})]
    )
    def test_missing_title(self, client: TestClient, admin_headers: dict[str, str], method: str, kwargs: dict) -> None:
        path = "/api/admin/titles/999" + ("/seasons" if method == "POST" else "")

        assert_error(client.request(method, path, headers=admin_headers, **kwargs), 404, "title_not_found")


class TestGenres:
    def test_create(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        r = client.post("/api/admin/genres", headers=admin_headers, json={"name": " Документальний "})

        assert r.status_code == 201
        assert r.json()["name"] == "Документальний"
        assert client.get("/api/genres").json() == [r.json()]

    @pytest.mark.parametrize("name", ["Drama", "DRAMA", " drama "])
    def test_create_duplicate(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int], name: str
    ) -> None:
        assert_error(client.post("/api/admin/genres", headers=admin_headers, json={"name": name}), 409, "genre_exists")

    @pytest.mark.parametrize("payload", [{"name": ""}, {"name": "x" * 81}, {}, {"name": None}])
    def test_create_validates(self, client: TestClient, admin_headers: dict[str, str], payload: dict) -> None:
        assert_error(client.post("/api/admin/genres", headers=admin_headers, json=payload), 422, "validation_error")

    def test_rename(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.patch(f"/api/admin/genres/{ids['drama']}", headers=admin_headers, json={"name": "Драма"})

        assert r.json() == {"id": ids["drama"], "name": "Драма"}
        assert client.get(f"/api/titles/{ids['series']}").json()["genres"][0]["name"] == "Драма"

    def test_rename_case_of_itself(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        r = client.patch(f"/api/admin/genres/{ids['drama']}", headers=admin_headers, json={"name": "DRAMA"})

        assert r.status_code == 200 and r.json()["name"] == "DRAMA"

    def test_rename_to_existing(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.patch(f"/api/admin/genres/{ids['drama']}", headers=admin_headers, json={"name": "comedy"})

        assert_error(r, 409, "genre_exists")

    def test_delete_detaches_from_titles(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        assert client.delete(f"/api/admin/genres/{ids['drama']}", headers=admin_headers).status_code == 204

        assert client.get(f"/api/titles/{ids['series']}").json()["genres"] == []
        assert count(Title) == 2

    @pytest.mark.parametrize(("method", "kwargs"), [("PATCH", {"json": {"name": "X"}}), ("DELETE", {})])
    def test_missing(self, client: TestClient, admin_headers: dict[str, str], method: str, kwargs: dict) -> None:
        r = client.request(method, "/api/admin/genres/999", headers=admin_headers, **kwargs)

        assert_error(r, 404, "genre_not_found")


class TestSeasonsAndEpisodes:
    def test_create_season(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.post(f"/api/admin/titles/{ids['series']}/seasons", headers=admin_headers, json={"number": 2})

        assert r.status_code == 201
        assert r.json()["number"] == 2 and r.json()["episodes"] == []
        assert [s["number"] for s in client.get(f"/api/titles/{ids['series']}").json()["seasons"]] == [1, 2]

    def test_season_requires_series(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        r = client.post(f"/api/admin/titles/{ids['movie']}/seasons", headers=admin_headers, json={"number": 1})

        assert_error(r, 409, "not_a_series")

    def test_duplicate_season(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.post(f"/api/admin/titles/{ids['series']}/seasons", headers=admin_headers, json={"number": 1})

        assert_error(r, 409, "season_exists")

    @pytest.mark.parametrize("payload", [{"number": 0}, {"number": "one"}, {}])
    def test_season_validates(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int], payload: dict
    ) -> None:
        r = client.post(f"/api/admin/titles/{ids['series']}/seasons", headers=admin_headers, json=payload)

        assert_error(r, 422, "validation_error")

    def test_update_season(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.patch(f"/api/admin/seasons/{ids['season']}", headers=admin_headers, json={"number": 3})

        assert r.status_code == 200
        assert r.json()["number"] == 3 and len(r.json()["episodes"]) == 2

    def test_update_season_conflict(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        client.post(f"/api/admin/titles/{ids['series']}/seasons", headers=admin_headers, json={"number": 2})

        r = client.patch(f"/api/admin/seasons/{ids['season']}", headers=admin_headers, json={"number": 2})

        assert_error(r, 409, "season_exists")

    def test_delete_season_cascades(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        assert client.delete(f"/api/admin/seasons/{ids['season']}", headers=admin_headers).status_code == 204

        assert (count(Season), count(Episode)) == (0, 0)
        assert client.get(f"/api/titles/{ids['series']}").json()["seasons"] == []

    def test_create_episode(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.post(
            f"/api/admin/seasons/{ids['season']}/episodes", headers=admin_headers, json={"number": 3, "name": " Past "}
        )

        assert r.status_code == 201
        assert {k: r.json()[k] for k in ("number", "name")} == {"number": 3, "name": "Past"}
        episodes = client.get(f"/api/titles/{ids['series']}").json()["seasons"][0]["episodes"]
        assert [e["name"] for e in episodes] == ["Secrets", "Lies", "Past"]

    def test_duplicate_episode(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.post(
            f"/api/admin/seasons/{ids['season']}/episodes", headers=admin_headers, json={"number": 1, "name": "X"}
        )

        assert_error(r, 409, "episode_exists")

    @pytest.mark.parametrize(
        "payload", [{"number": 1}, {"name": "X"}, {"number": 0, "name": "X"}, {"number": 9, "name": ""}]
    )
    def test_episode_validates(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int], payload: dict
    ) -> None:
        r = client.post(f"/api/admin/seasons/{ids['season']}/episodes", headers=admin_headers, json=payload)

        assert_error(r, 422, "validation_error")

    def test_update_episode(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.patch(f"/api/admin/episodes/{ids['episode']}", headers=admin_headers, json={"name": "Geheimnisse"})

        assert r.status_code == 200
        assert (r.json()["number"], r.json()["name"]) == (1, "Geheimnisse")

    def test_update_episode_conflict(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        r = client.patch(f"/api/admin/episodes/{ids['episode']}", headers=admin_headers, json={"number": 2})

        assert_error(r, 409, "episode_exists")

    def test_delete_episode(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        assert client.delete(f"/api/admin/episodes/{ids['episode']}", headers=admin_headers).status_code == 204

        episodes = client.get(f"/api/titles/{ids['series']}").json()["seasons"][0]["episodes"]
        assert [e["name"] for e in episodes] == ["Lies"]

    @pytest.mark.parametrize(
        ("method", "path", "kwargs", "code"),
        [
            ("PATCH", "/api/admin/seasons/999", {"json": {"number": 1}}, "season_not_found"),
            ("DELETE", "/api/admin/seasons/999", {}, "season_not_found"),
            ("POST", "/api/admin/seasons/999/episodes", {"json": {"number": 1, "name": "X"}}, "season_not_found"),
            ("PATCH", "/api/admin/episodes/999", {"json": {"name": "X"}}, "episode_not_found"),
            ("DELETE", "/api/admin/episodes/999", {}, "episode_not_found"),
        ],
    )
    def test_missing(
        self, client: TestClient, admin_headers: dict[str, str], method: str, path: str, kwargs: dict, code: str
    ) -> None:
        assert_error(client.request(method, path, headers=admin_headers, **kwargs), 404, code)


class TestPoster:
    def upload(self, client: TestClient, headers: dict[str, str], title_id: int, content: bytes, mime: str) -> Any:
        return client.post(
            f"/api/admin/titles/{title_id}/poster", headers=headers, files={"file": ("poster", content, mime)}
        )

    @pytest.mark.parametrize(
        ("content", "mime", "ext"),
        [(PNG, "image/png", "png"), (JPEG, "image/jpeg", "jpg"), (WEBP, "image/webp", "webp")],
    )
    def test_upload_and_serve(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        ids: dict[str, int],
        content: bytes,
        mime: str,
        ext: str,
    ) -> None:
        r = self.upload(client, admin_headers, ids["movie"], content, mime)

        assert r.status_code == 200, r.text
        url = r.json()["poster_url"]
        assert url.startswith(f"/media/posters/{ids['movie']}-") and url.endswith(f".{ext}")
        assert client.get(f"/api/titles/{ids['movie']}").json()["poster_url"] == url
        served = client.get(url)
        assert served.status_code == 200 and served.content == content

    def test_replacing_removes_old_file(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        old = self.upload(client, admin_headers, ids["movie"], PNG, "image/png").json()["poster_url"]

        new = self.upload(client, admin_headers, ids["movie"], JPEG, "image/jpeg").json()["poster_url"]

        assert new != old
        assert not poster_path(old).exists() and poster_path(new).exists()

    def test_deleting_title_removes_poster(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        url = self.upload(client, admin_headers, ids["movie"], PNG, "image/png").json()["poster_url"]

        client.delete(f"/api/admin/titles/{ids['movie']}", headers=admin_headers)

        assert not poster_path(url).exists()

    @pytest.mark.parametrize(
        ("content", "mime"),
        [
            (b"GIF89a" + b"\x00" * 64, "image/gif"),
            (b"plain text", "text/plain"),
            (b"plain text", "image/png"),
            (PNG, "image/jpeg"),
            (b"", "image/png"),
        ],
    )
    def test_rejects_non_images(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int], content: bytes, mime: str
    ) -> None:
        r = self.upload(client, admin_headers, ids["movie"], content, mime)

        assert_error(r, 415, "unsupported_media_type")
        assert client.get(f"/api/titles/{ids['movie']}").json()["poster_url"] is None

    def test_accepts_exactly_max_size(
        self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]
    ) -> None:
        content = PNG + b"\x00" * (MAX_POSTER_BYTES - len(PNG))

        assert self.upload(client, admin_headers, ids["movie"], content, "image/png").status_code == 200

    def test_rejects_too_large(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        content = PNG + b"\x00" * (MAX_POSTER_BYTES - len(PNG) + 1)

        assert_error(self.upload(client, admin_headers, ids["movie"], content, "image/png"), 413, "payload_too_large")

    def test_requires_file(self, client: TestClient, admin_headers: dict[str, str], ids: dict[str, int]) -> None:
        r = client.post(f"/api/admin/titles/{ids['movie']}/poster", headers=admin_headers)

        assert_error(r, 422, "validation_error")

    def test_missing_title(self, client: TestClient, admin_headers: dict[str, str]) -> None:
        assert_error(self.upload(client, admin_headers, 999, PNG, "image/png"), 404, "title_not_found")
