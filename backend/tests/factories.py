from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Episode, Genre, Profile, Season, Title, TitleKind, User, WatchHistory


def make_genre(session: Session, name: str) -> Genre:
    genre = Genre(name=name)
    session.add(genre)
    session.flush()
    return genre


def make_title(session: Session, name: str, genres: list[Genre] | None = None, **fields: Any) -> Title:
    defaults: dict[str, Any] = {
        "kind": TitleKind.MOVIE.value,
        "description": "",
        "year": 2000,
        "country": "USA",
        "rating": 5.0,
    }
    title = Title(name=name, genres=genres or [], **(defaults | fields))
    session.add(title)
    session.flush()
    return title


def add_season(session: Session, title: Title, number: int, episode_names: list[str]) -> Season:
    season = Season(
        title=title,
        number=number,
        episodes=[Episode(number=i, name=n) for i, n in enumerate(episode_names, start=1)],
    )
    session.add(season)
    session.flush()
    return season


def add_views(session: Session, title: Title, user_ids: Iterable[int], episode: Episode | None = None) -> None:
    session.add_all(
        WatchHistory(user_id=user_id, title_id=title.id, episode_id=episode.id if episode else None)
        for user_id in user_ids
    )
    session.flush()


def add_history(
    session: Session,
    user_id: int,
    title: Title,
    *,
    episode: Episode | None = None,
    finished: bool = False,
    progress_sec: int = 60,
    last_watched: datetime | None = None,
) -> WatchHistory:
    entry = WatchHistory(
        user_id=user_id,
        title_id=title.id,
        episode_id=episode.id if episode else None,
        progress_sec=progress_sec,
        finished=finished,
    )
    if last_watched is not None:
        entry.last_watched = last_watched
    session.add(entry)
    session.flush()
    return entry


def make_user(session: Session, email: str, created_at: datetime | None = None) -> User:
    user = User(email=email, password_hash=hash_password("x"), profile=Profile(display_name=email.split("@")[0]))
    if created_at is not None:
        user.created_at = created_at
    session.add(user)
    session.flush()
    return user
