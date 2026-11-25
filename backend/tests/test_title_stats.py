from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.events import WatchFinished
from app.models import TitleKind, TitleStats, TitleViewer
from app.repositories.title_stats_repository import TitleStatsRepository
from app.services.title_stats import TitleStatsService, TitleStatsUpdater
from app.tools.rebuild_stats import main
from tests.factories import add_history, add_season, make_title, make_user
from tests.helpers import PASSWORD, bearer, login, register


class FakeRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def record_completion(self, title_id: int, user_id: int) -> bool:
        self.calls.append((title_id, user_id))
        return True


@pytest.fixture
def catalog() -> dict[str, int]:
    with SessionLocal() as session, session.begin():
        heat = make_title(session, "Heat")
        dark = make_title(session, "Dark", kind=TitleKind.SERIES.value)
        first, second = add_season(session, dark, 1, ["Secrets", "Lies"]).episodes
        return {"heat": heat.id, "dark": dark.id, "e1": first.id, "e2": second.id}


def put_progress(client: TestClient, headers: dict[str, str], **body: Any) -> None:
    r = client.put("/api/history/progress", json=body, headers=headers)
    assert r.status_code == 200, r.text


def stats(title_id: int) -> tuple[int, int] | None:
    with SessionLocal() as session:
        row = TitleStatsRepository(session).get(title_id)
        return None if row is None else (row.unique_viewers, row.completions)


def all_stats() -> dict[int, tuple[int, int]]:
    with SessionLocal() as session:
        return {s.title_id: (s.unique_viewers, s.completions) for s in session.scalars(select(TitleStats))}


def headers_for(client: TestClient, email: str) -> dict[str, str]:
    register(client, email)
    return bearer(login(client, email, PASSWORD).json()["access_token"])


def test_updater_records_completion_in_the_publisher_session() -> None:
    recorder = FakeRecorder()
    sessions: list[Session] = []

    def factory(session: Session) -> FakeRecorder:
        sessions.append(session)
        return recorder

    session = Session()
    TitleStatsUpdater(factory).handle(WatchFinished(user_id=7, title_id=3, episode_id=None), session)

    assert recorder.calls == [(3, 7)]
    assert sessions == [session]


def test_finishing_a_title_creates_stats(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=100)
    assert stats(catalog["heat"]) is None

    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=5400, finished=True)

    assert stats(catalog["heat"]) == (1, 1)
    with SessionLocal() as session:
        assert TitleStatsRepository(session).get(catalog["heat"]).last_watched_at is not None


def test_repeated_completion_by_the_same_user_counts_once_as_viewer(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    for progress, finished in [(5400, True), (5400, True), (20, False), (5400, True)]:
        put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=progress, finished=finished)

    assert stats(catalog["heat"]) == (1, 2)

    put_progress(client, headers_for(client, "second@example.com"),
                 title_id=catalog["heat"], progress_sec=5400, finished=True)

    assert stats(catalog["heat"]) == (2, 3)


def test_series_episodes_of_one_user_add_completions_but_one_viewer(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    for episode in ("e1", "e2"):
        put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog[episode],
                     progress_sec=3000, finished=True)

    assert stats(catalog["dark"]) == (1, 2)


def test_rebuild_matches_incremental_stats(
    client: TestClient, user_headers: dict[str, str], catalog: dict[str, int]
) -> None:
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=5400, finished=True)
    put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e1"],
                 progress_sec=3000, finished=True)
    put_progress(client, user_headers, title_id=catalog["dark"], episode_id=catalog["e2"],
                 progress_sec=3000, finished=True)
    put_progress(client, headers_for(client, "second@example.com"),
                 title_id=catalog["dark"], episode_id=catalog["e1"], progress_sec=3000, finished=True)
    incremental = all_stats()

    with SessionLocal() as session, session.begin():
        totals = TitleStatsService(TitleStatsRepository(session)).rebuild()

    assert all_stats() == incremental == {catalog["heat"]: (1, 1), catalog["dark"]: (2, 3)}
    assert (totals.titles, totals.viewers, totals.completions) == (2, 3, 4)


def test_rebuild_drops_stale_rows_and_ignores_unfinished_history() -> None:
    with SessionLocal() as session, session.begin():
        heat, ronin, alien = (make_title(session, n) for n in ("Heat", "Ronin", "Alien"))
        anna, bob = make_user(session, "anna@example.com"), make_user(session, "bob@example.com")
        add_history(session, anna.id, heat, finished=True)
        add_history(session, bob.id, heat, finished=True)
        add_history(session, bob.id, ronin, finished=False)
        session.add(TitleStats(title_id=alien.id, unique_viewers=9, completions=9))
        session.add(TitleViewer(title_id=alien.id, user_id=anna.id))
        heat_id, alien_id = heat.id, alien.id

    with SessionLocal() as session, session.begin():
        TitleStatsService(TitleStatsRepository(session)).rebuild()

    assert all_stats() == {heat_id: (2, 2)}
    with SessionLocal() as session:
        viewers = set(session.execute(select(TitleViewer.title_id, TitleViewer.user_id)).all())
        assert len(viewers) == 2 and all(title_id != alien_id for title_id, _ in viewers)


def test_rebuilt_viewers_keep_later_completions_idempotent(client: TestClient, user_headers: dict[str, str],
                                                           catalog: dict[str, int]) -> None:
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=5400, finished=True)
    with SessionLocal() as session, session.begin():
        TitleStatsService(TitleStatsRepository(session)).rebuild()

    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=10, finished=False)
    put_progress(client, user_headers, title_id=catalog["heat"], progress_sec=5400, finished=True)

    assert stats(catalog["heat"]) == (1, 2)


def test_rebuild_command_prints_totals(capsys: pytest.CaptureFixture[str]) -> None:
    with SessionLocal() as session, session.begin():
        heat = make_title(session, "Heat")
        add_history(session, make_user(session, "anna@example.com").id, heat, finished=True)

    assert main([]) == 0

    assert capsys.readouterr().out.strip() == "Rebuilt stats: 1 titles, 1 viewers, 1 completions"
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(TitleStats)) == 1
