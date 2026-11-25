from collections.abc import Collection, Mapping, Sequence
from datetime import datetime

from sqlalchemy import ColumnElement, Select, case, func, or_, select
from sqlalchemy.orm import Session

from app.models import Favorite, Genre, Title, TitleStats, WatchHistory, title_genres
from app.patterns.recommendation import PopularTitle, TitleFeatures
from app.services.ports import UserTaste


def _features(title: Title) -> TitleFeatures:
    return TitleFeatures(
        id=title.id,
        name=title.name,
        year=title.year,
        country=title.country,
        rating=title.rating,
        genre_ids=frozenset(g.id for g in title.genres),
    )


class RecommendationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def popular(self, since: datetime, exclude: Collection[int], limit: int) -> Sequence[PopularTitle]:
        window = (
            select(
                WatchHistory.title_id,
                func.count(WatchHistory.user_id.distinct()).label("viewers"),
                func.count().filter(WatchHistory.finished.is_(True)).label("completions"),
            )
            .where(WatchHistory.last_watched >= since)
            .group_by(WatchHistory.title_id)
            .subquery()
        )
        window_viewers = func.coalesce(window.c.viewers, 0)
        window_completions = func.coalesce(window.c.completions, 0)
        total_viewers = func.coalesce(TitleStats.unique_viewers, 0)
        total_completions = func.coalesce(TitleStats.completions, 0)
        tier = case((window_viewers > 0, 0), (total_viewers > 0, 1), else_=2)
        statement = (
            select(Title.id, window_viewers, window_completions, total_viewers, total_completions, Title.rating)
            .outerjoin(window, window.c.title_id == Title.id)
            .outerjoin(TitleStats, TitleStats.title_id == Title.id)
            .where(*self._not_in(exclude))
            .order_by(tier, window_viewers.desc(), window_completions.desc(), total_viewers.desc(),
                      total_completions.desc(), Title.rating.desc(), Title.id)
            .limit(limit)
        )
        return [PopularTitle(*row) for row in self.session.execute(statement)]

    def features(self, title_ids: Collection[int]) -> Mapping[int, TitleFeatures]:
        ids = list(title_ids)
        if not ids:
            return {}
        return {t.id: _features(t) for t in self.session.scalars(select(Title).where(Title.id.in_(ids)))}

    def candidates(self, genre_ids: Collection[int], exclude: Collection[int], limit: int) -> Sequence[TitleFeatures]:
        if not genre_ids:
            return []
        return self._load(select(Title).where(self._tagged(genre_ids), *self._not_in(exclude)), limit)

    def similar_candidates(
        self, seed: TitleFeatures, exclude: Collection[int], limit: int
    ) -> Sequence[TitleFeatures]:
        same_country = func.lower(Title.country) == seed.country.lower()
        related = or_(self._tagged(seed.genre_ids), same_country) if seed.genre_ids else same_country
        return self._load(select(Title).where(related, *self._not_in(exclude)), limit)

    def genre_names(self, genre_ids: Collection[int]) -> Mapping[int, str]:
        ids = list(genre_ids)
        if not ids:
            return {}
        rows = self.session.execute(select(Genre.id, Genre.name).where(Genre.id.in_(ids)))
        return {genre_id: name for genre_id, name in rows}

    def taste(self, user_id: int) -> UserTaste:
        rows = self.session.execute(
            select(WatchHistory.title_id, func.bool_or(WatchHistory.finished), func.max(WatchHistory.last_watched))
            .where(WatchHistory.user_id == user_id)
            .group_by(WatchHistory.title_id)
        ).all()
        favorites = self.session.scalars(select(Favorite.title_id).where(Favorite.user_id == user_id))
        finished = [(last, title_id) for title_id, done, last in rows if done]
        recent = finished or [(last, title_id) for title_id, _, last in rows]
        return UserTaste(
            watched=frozenset(title_id for title_id, _, _ in rows),
            finished=frozenset(title_id for _, title_id in finished),
            favorites=frozenset(favorites),
            last_watched_title_id=max(recent)[1] if recent else None,
        )

    def _load(self, statement: Select[tuple[Title]], limit: int) -> list[TitleFeatures]:
        titles = self.session.scalars(statement.order_by(Title.rating.desc(), Title.id).limit(limit))
        return [_features(t) for t in titles]

    @staticmethod
    def _tagged(genre_ids: Collection[int]) -> ColumnElement[bool]:
        return Title.id.in_(select(title_genres.c.title_id).where(title_genres.c.genre_id.in_(list(genre_ids))))

    @staticmethod
    def _not_in(exclude: Collection[int]) -> list[ColumnElement[bool]]:
        return [Title.id.not_in(list(exclude))] if exclude else []
