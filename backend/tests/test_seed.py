from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import verify_password
from app.demo_data import DEMO_GENRES, DEMO_TITLES
from app.models import Episode, Genre, Plan, PlanCode, Role, Season, Title, TitleKind, User
from app.seed import main, seed, seed_demo_catalog


def _run_seed() -> None:
    with SessionLocal() as session, session.begin():
        seed(session)


def test_seed_creates_plans_and_admin() -> None:
    _run_seed()

    with SessionLocal() as session:
        plans = {p.code: p for p in session.scalars(select(Plan))}
        admin = session.scalar(select(User).where(User.email == settings.admin_email))

    assert set(plans) == {PlanCode.FREE, PlanCode.PREMIUM}
    free, premium = plans[PlanCode.FREE], plans[PlanCode.PREMIUM]
    assert (free.ads_enabled, free.max_height, free.price_month) == (True, 720, Decimal("0.00"))
    assert (premium.ads_enabled, premium.max_height, premium.price_month) == (False, 1080, Decimal("99.00"))
    assert admin is not None and admin.role == Role.ADMIN and admin.profile is not None
    assert verify_password(settings.admin_password, admin.password_hash)


def test_seed_is_idempotent_and_restores_reference_values() -> None:
    _run_seed()
    with SessionLocal() as session, session.begin():
        session.scalar(select(Plan).where(Plan.code == PlanCode.PREMIUM)).price_month = Decimal("1.00")
        admin = session.scalar(select(User).where(User.email == settings.admin_email))
        admin.role = Role.USER
        original_hash = admin.password_hash

    _run_seed()

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Plan)) == 2
        assert session.scalar(select(func.count()).select_from(User)) == 1
        premium = session.scalar(select(Plan).where(Plan.code == PlanCode.PREMIUM))
        admin = session.scalar(select(User).where(User.email == settings.admin_email))
    assert premium.price_month == Decimal("99.00")
    assert admin.role == Role.ADMIN
    assert admin.password_hash == original_hash


def _run_demo_seed() -> None:
    with SessionLocal() as session, session.begin():
        seed_demo_catalog(session)


def _demo_title(session: Session, name: str) -> Title:
    return session.scalar(
        select(Title).where(Title.name == name).options(selectinload(Title.seasons).selectinload(Season.episodes))
    )


def _catalog_counts(session: Session) -> tuple[int, ...]:
    return tuple(session.scalar(select(func.count()).select_from(model)) for model in (Genre, Title, Season, Episode))


def test_demo_data_is_consistent() -> None:
    assert len(set(DEMO_GENRES)) == len(DEMO_GENRES) == 12
    assert len({(t.kind, t.name, t.year) for t in DEMO_TITLES}) == len(DEMO_TITLES)
    assert {g for t in DEMO_TITLES for g in t.genres} == set(DEMO_GENRES)
    assert all(0 <= t.rating <= 10 and t.description for t in DEMO_TITLES)


def test_demo_seed_creates_catalog() -> None:
    _run_demo_seed()

    with SessionLocal() as session:
        titles = session.scalars(select(Title)).all()
        series = [t for t in titles if t.kind == TitleKind.SERIES]
        movies = [t for t in titles if t.kind == TitleKind.MOVIE]
        assert len(movies) == 25 and len(series) == 6
        assert all(t.genres for t in titles)
        assert all(t.poster_url is None for t in titles)
        assert len({t.country for t in titles}) >= 8
        assert all(t.seasons and all(s.episodes for s in t.seasons) for t in series)
        assert all(not t.seasons for t in movies)

        dark = _demo_title(session, "Темрява")
        assert [(s.number, len(s.episodes)) for s in dark.seasons] == [(1, 10), (2, 8), (3, 8)]
        assert [e.name for e in dark.seasons[0].episodes[:2]] == ["Серія 1", "Серія 2"]


def test_demo_seed_is_idempotent_and_keeps_admin_content() -> None:
    _run_demo_seed()
    with SessionLocal() as session, session.begin():
        before = _catalog_counts(session)
        matrix = _demo_title(session, "Матриця")
        matrix.rating = 1.0
        matrix.poster_url = "/media/posters/matrix.webp"
        chernobyl = _demo_title(session, "Чорнобиль")
        chernobyl.seasons[0].episodes[0].name = "1:23:45"
        session.delete(chernobyl.seasons[0].episodes[-1])

    _run_demo_seed()

    with SessionLocal() as session:
        assert _catalog_counts(session) == before
        matrix = _demo_title(session, "Матриця")
        assert matrix.rating == 8.7
        assert matrix.poster_url == "/media/posters/matrix.webp"
        episodes = _demo_title(session, "Чорнобиль").seasons[0].episodes
        assert [e.number for e in episodes] == [1, 2, 3, 4, 5]
        assert episodes[0].name == "1:23:45"


def test_main_loads_demo_catalog_only_with_flag(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Title)) == 0

    main(["--demo"])

    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Title)) == len(DEMO_TITLES)
        assert session.scalar(select(func.count()).select_from(Plan)) == 2
    assert "Demo catalog: 12 genres, 31 titles" in capsys.readouterr().out
