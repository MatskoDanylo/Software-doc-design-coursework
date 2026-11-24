from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.core.events import DomainEvent, WatchFinished
from app.models import TitleKind, User, VideoAsset, VideoStatus, WatchHistory
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.history_repository import WatchHistoryRepository
from app.repositories.season_repository import EpisodeRepository
from app.repositories.title_repository import TitleRepository
from app.repositories.users import UserRepository
from app.schemas.history import ProgressUpdate
from app.services.history_service import HistoryService
from app.services.playback_target import PlaybackTargetResolver
from tests.factories import add_season, make_title
from tests.helpers import PASSWORD, assert_error, bearer, login, register


@pytest.fixture
def catalog() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        heat = make_title(session, "Heat")
        ronin = make_title(session, "Ronin")
        dark = make_title(session, "Dark", kind=TitleKind.SERIES.value)
        lost = make_title(session, "Lost", kind=TitleKind.SERIES.value)
        first, second = add_season(session, dark, 1, ["Secrets", "Lies"]).episodes
        add_season(session, dark, 2, ["Ghosts"])
        pilot = add_season(session, lost, 1, ["Pilot"]).episodes[0]
        return {"heat": heat.id, "ronin": ronin.id, "dark": dark.id, "lost": lost.id,
                "e1": first.id, "e2": second.id, "pilot": pilot.id}


def put_progress(client: TestClient, headers: dict[str, str], **body: Any) -> dict[str, Any]:
    r = client.put("/api/history/progress", json=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def continue_watching(client: TestClient, headers: dict[str, str], **params: int) -> list[dict[str, Any]]:
    r = client.get("/api/history", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def history_rows() -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(WatchHistory)) or 0


def test_progress_is_upserted_per_title(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=30)
    body = put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=95)

    assert history_rows() == 1
    assert (body["progress_sec"], body["finished"], body["episode"]) == (95, False, None)
    assert (body["title"]["id"], body["title"]["name"]) == (catalog["heat"], "Heat")
    assert body["last_watched"]


def test_episodes_have_separate_progress(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e1"], progress_sec=10)
    body = put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e2"], progress_sec=20)
    put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e2"], progress_sec=40)

    assert history_rows() == 2
    assert body["episode"] == {"id": catalog["e2"], "number": 2, "name": "Lies", "season_number": 1}


def test_continue_watching_is_most_recent_first(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=30)
    put_progress(client, user_headers, title_id=catalog["ronin"], progress_sec=60)
    put_progress(client, user_headers, title_id=catalog["lost"], episode_id=catalog["pilot"], progress_sec=5)
    assert [e["title"]["name"] for e in continue_watching(client, user_headers)] == ["Lost", "Ronin", "Heat"]

    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=45)

    entries = continue_watching(client, user_headers)
    assert [(e["title"]["name"], e["progress_sec"]) for e in entries] == [("Heat", 45), ("Lost", 5), ("Ronin", 60)]
    assert [e["title"]["name"] for e in continue_watching(client, user_headers, limit=2)] == ["Heat", "Lost"]


def test_finished_and_unstarted_entries_are_hidden(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=300)
    put_progress(client, user_headers, title_id=catalog["ronin"], progress_sec=0)
    finished = put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=7200, finished=True)

    assert finished["finished"] is True
    assert continue_watching(client, user_headers) == []

    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=12)

    assert [(e["title"]["name"], e["finished"]) for e in continue_watching(client, user_headers)] == [("Heat", False)]


def test_series_shows_only_latest_unfinished_episode(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e1"], progress_sec=100)
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=50)
    put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e2"], progress_sec=200)

    entries = continue_watching(client, user_headers)

    assert [(e["title"]["name"], e["episode"] and e["episode"]["id"]) for e in entries] == [
        ("Dark", catalog["e2"]), ("Heat", None),
    ]


def test_history_marks_favorite_titles(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    client.post(f"/api/favorites/{catalog['heat']}", headers=user_headers)

    body = put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=30)
    put_progress(client, user_headers, title_id=catalog["ronin"], progress_sec=30)

    assert body["title"]["is_favorite"] is True
    assert {e["title"]["name"]: e["title"]["is_favorite"] for e in continue_watching(client, user_headers)} == {
        "Heat": True, "Ronin": False,
    }


def test_entries_carry_duration_of_ready_video(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    with SessionLocal() as session, session.begin():
        session.add_all([
            VideoAsset(title_id=catalog["heat"], status=VideoStatus.READY, duration_sec=5400),
            VideoAsset(episode_id=catalog["e1"], status=VideoStatus.READY, duration_sec=2700),
            VideoAsset(title_id=catalog["ronin"], status=VideoStatus.PROCESSING, duration_sec=None),
        ])
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=60)
    put_progress(client, user_headers, title_id=catalog["ronin"], progress_sec=60)
    put_progress(client, user_headers, title_id=catalog["lost"], episode_id=catalog["pilot"], progress_sec=60)
    body = put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e1"], progress_sec=60)

    assert body["duration_sec"] == 2700
    assert {e["title"]["name"]: e["duration_sec"] for e in continue_watching(client, user_headers)} == {
        "Heat": 5400, "Ronin": None, "Lost": None, "Dark": 2700,
    }


def test_history_is_per_user(client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]) -> None:
    register(client, "other@example.com")
    other = bearer(login(client, "other@example.com", PASSWORD).json()["access_token"])
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=30)
    put_progress(client, other, title_id=catalog["heat"], progress_sec=90)

    assert history_rows() == 2
    assert [e["progress_sec"] for e in continue_watching(client, user_headers)] == [30]


@pytest.mark.parametrize(
    ("body", "status", "code"),
    [
        ({"title_id": "dark", "progress_sec": 1}, 422, "episode_required"),
        ({"title_id": "heat", "episode_id": "e1", "progress_sec": 1}, 422, "episode_not_allowed"),
        ({"title_id": "dark", "episode_id": "pilot", "progress_sec": 1}, 404, "episode_not_found"),
        ({"title_id": "missing", "progress_sec": 1}, 404, "title_not_found"),
        ({"title_id": "heat", "progress_sec": -1}, 422, "validation_error"),
        ({"title_id": "heat", "progress_sec": 86401}, 422, "validation_error"),
        ({"title_id": "heat", "progress_sec": 1, "user_id": 5}, 422, "validation_error"),
    ],
)
def test_progress_validation(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int],
    body: dict[str, Any], status: int, code: str,
) -> None:
    payload = {k: catalog.get(v, 999) if k in {"title_id", "episode_id"} else v for k, v in body.items()}

    assert_error(client.put("/api/history/progress", json=payload, headers=user_headers), status, code)
    assert history_rows() == 0


def test_history_requires_authentication(client: TestClient) -> None:
    assert_error(client.get("/api/history"), 401, "unauthorized")
    assert_error(client.put("/api/history/progress", json={"title_id": 1, "progress_sec": 1}), 401, "unauthorized")


def test_deleting_episode_removes_its_progress(
    client: TestClient, user_headers: dict[str, str], admin_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    for episode in ("e1", "e2"):
        put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog[episode], progress_sec=10)

    assert client.delete(f"/api/admin/episodes/{catalog['e1']}", headers=admin_headers).status_code == 204
    assert client.delete(f"/api/admin/episodes/{catalog['e2']}", headers=admin_headers).status_code == 204

    assert history_rows() == 0


class RecordingPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


def test_just_finished_is_reported_only_on_transition(user_headers: dict[str, str], catalog: dict[str, int]) -> None:
    steps = [(100, False), (5400, True), (5400, True), (20, False), (5400, True)]
    flags = []
    publisher = RecordingPublisher()
    for progress, finished in steps:
        with SessionLocal() as session, session.begin():
            user = UserRepository(session).get_by_email("user@example.com")
            assert isinstance(user, User)
            user_id = user.id
            service = HistoryService(
                WatchHistoryRepository(session),
                PlaybackTargetResolver(TitleRepository(session), EpisodeRepository(session)),
                FavoriteRepository(session),
                publisher,
            )
            result = service.record_progress(
                user, ProgressUpdate(title_id=catalog["heat"], progress_sec=progress, finished=finished)
            )
            flags.append(result.just_finished)

    assert flags == [False, True, False, False, True]
    event = WatchFinished(user_id=user_id, title_id=catalog["heat"], episode_id=None)
    assert publisher.events == [event, event]
