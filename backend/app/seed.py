import argparse
from collections.abc import Iterable, Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.demo_activity import DEMO_PASSWORD, EMAIL_TEMPLATE, DemoActivitySummary, seed_demo_activity
from app.demo_data import DEMO_GENRES, DEMO_TITLES, DemoTitle, episode_name
from app.models import Episode, Genre, Plan, PlanCode, Role, Season, Title
from app.repositories.genre_repository import GenreRepository
from app.repositories.plans import PlanRepository
from app.repositories.title_repository import TitleRepository
from app.repositories.users import UserRepository
from app.schemas.common import normalize_email
from app.services.users import UserService

PLANS: tuple[dict[str, Any], ...] = (
    {
        "code": PlanCode.FREE,
        "name": "Безкоштовний",
        "price_month": Decimal("0.00"),
        "ads_enabled": True,
        "max_height": 720,
    },
    {
        "code": PlanCode.PREMIUM,
        "name": "Преміум",
        "price_month": Decimal("99.00"),
        "ads_enabled": False,
        "max_height": 1080,
    },
)


def seed_plans(session: Session) -> None:
    repo = PlanRepository(session)
    for spec in PLANS:
        plan = repo.get_by_code(spec["code"])
        if plan is None:
            repo.add(Plan(**spec))
            continue
        for field, value in spec.items():
            setattr(plan, field, value)


def seed_admin(session: Session, email: str, password: str) -> None:
    users = UserRepository(session)
    admin = users.get_by_email(normalize_email(email))
    if admin is None:
        UserService(users).create(email, password, "Administrator", Role.ADMIN)
    elif admin.role != Role.ADMIN:
        admin.role = Role.ADMIN


def seed(session: Session) -> None:
    seed_plans(session)
    seed_admin(session, settings.admin_email, settings.admin_password)


def _seed_genres(session: Session, names: Iterable[str]) -> dict[str, Genre]:
    repo = GenreRepository(session)
    return {name: repo.get_by_name(name) or repo.add(Genre(name=name)) for name in names}


def _sync_seasons(title: Title, episode_counts: Sequence[int]) -> None:
    seasons = {s.number: s for s in title.seasons}
    for number, count in enumerate(episode_counts, start=1):
        season = seasons.get(number)
        if season is None:
            season = Season(number=number)
            title.seasons.append(season)
        existing = {e.number for e in season.episodes}
        season.episodes.extend(
            Episode(number=n, name=episode_name(n)) for n in range(1, count + 1) if n not in existing
        )


def _seed_title(titles: TitleRepository, spec: DemoTitle, genres: dict[str, Genre]) -> None:
    title = titles.get_by_identity(spec.kind, spec.name, spec.year)
    if title is None:
        title = titles.add(Title(kind=spec.kind.value, name=spec.name, year=spec.year, country=spec.country))
    title.description = spec.description
    title.country = spec.country
    title.rating = spec.rating
    title.genres = [genres[g] for g in spec.genres]
    _sync_seasons(title, spec.seasons)


def seed_demo_catalog(session: Session) -> None:
    genres = _seed_genres(session, DEMO_GENRES)
    titles = TitleRepository(session)
    for spec in DEMO_TITLES:
        _seed_title(titles, spec, genres)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.seed", description="Seed reference data.")
    parser.add_argument("--demo", action="store_true", help="also load the demo catalog (genres, movies, series)")
    parser.add_argument(
        "--demo-activity",
        action="store_true",
        help="recreate demo users with watch history, favorites and payments (implies --demo)",
    )
    args = parser.parse_args(argv)
    load_catalog = args.demo or args.demo_activity

    activity: DemoActivitySummary | None = None
    with SessionLocal() as session, session.begin():
        seed(session)
        if load_catalog:
            seed_demo_catalog(session)
        if args.demo_activity:
            activity = seed_demo_activity(session)

    print(f"Seed complete: plans {[p['code'].value for p in PLANS]}, admin {settings.admin_email}")
    if load_catalog:
        print(f"Demo catalog: {len(DEMO_GENRES)} genres, {len(DEMO_TITLES)} titles")
    if activity is not None:
        payments = ", ".join(f"{status} {count}" for status, count in sorted(activity.payments.items()))
        print(
            f"Demo activity: {activity.users} users, {activity.history} history entries, "
            f"{activity.favorites} favorites, payments: {payments}, active Premium {activity.active_premium}"
        )
        print(
            f"Demo login: {EMAIL_TEMPLATE.format(1)} ... {EMAIL_TEMPLATE.format(activity.users)}, "
            f"password {DEMO_PASSWORD}"
        )


if __name__ == "__main__":
    main()
