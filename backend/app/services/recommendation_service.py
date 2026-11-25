from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Protocol

from app.core.errors import NotFoundError
from app.models import User
from app.patterns.recommendation import (
    PopularityStrategy,
    RecommendationConfig,
    RecommendationContext,
    RecommendationSource,
    ScoredTitle,
    SimilarTitlesStrategy,
    StrategyEnv,
    StrategyRegistry,
)
from app.schemas.recommendation import RecommendationList, RecommendationRead
from app.services.favorite_service import mark_favorites
from app.services.ports import FavoriteReader, TitleBatchReader, UserTasteReader
from app.services.subscription_service import utc_now


class RecommendationConfigProvider(Protocol):
    def recommendation_config(self) -> RecommendationConfig: ...


class RecommendationService:
    def __init__(
        self,
        registry: StrategyRegistry,
        source: RecommendationSource,
        taste: UserTasteReader,
        titles: TitleBatchReader,
        favorites: FavoriteReader,
        config: RecommendationConfigProvider,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.registry = registry
        self.source = source
        self.taste = taste
        self.titles = titles
        self.favorites = favorites
        self.config = config
        self.clock = clock

    def recommend(self, user: User | None, limit: int, strategy_code: str | None = None) -> RecommendationList:
        if strategy_code is not None:
            self.registry.ensure_known(strategy_code)
        env = self._env()
        context = self._context(user)
        code = self.choose_strategy(context, strategy_code or env.config.default_strategy)
        items = env.create(code).recommend(context, limit)
        if code != PopularityStrategy.code and len(items) < limit:
            items = self._fill_with_popular(env, context, items, limit)
        return RecommendationList(strategy=code, items=self._read(items, user))

    def similar(self, title_id: int, limit: int, user: User | None) -> list[RecommendationRead]:
        if title_id not in self.source.features([title_id]):
            raise NotFoundError("Title not found", code="title_not_found")
        context = replace(self._context(user), seed_title_id=title_id)
        return self._read(self._env().create(SimilarTitlesStrategy.code).recommend(context, limit), user)

    @staticmethod
    def choose_strategy(context: RecommendationContext, requested: str) -> str:
        if context.user_id is None or not context.has_taste:
            return PopularityStrategy.code
        return requested

    def _env(self) -> StrategyEnv:
        return StrategyEnv(self.source, self.config.recommendation_config(), self.clock, self.registry)

    def _context(self, user: User | None) -> RecommendationContext:
        if user is None:
            return RecommendationContext()
        taste = self.taste.taste(user.id)
        return RecommendationContext(
            user_id=user.id,
            watched=taste.watched,
            finished=taste.finished,
            favorites=taste.favorites,
            seed_title_id=taste.last_watched_title_id,
        )

    @staticmethod
    def _fill_with_popular(
        env: StrategyEnv, context: RecommendationContext, items: list[ScoredTitle], limit: int
    ) -> list[ScoredTitle]:
        chosen = {item.title_id for item in items}
        floor = min((item.score for item in items), default=1.0)
        popular = env.create(PopularityStrategy.code).recommend(context, limit + len(items))
        extra = [replace(p, score=floor * p.score) for p in popular if p.title_id not in chosen]
        return items + extra[:limit - len(items)]

    def _read(self, items: Sequence[ScoredTitle], user: User | None) -> list[RecommendationRead]:
        titles = {t.id: t for t in self.titles.get_many([item.title_id for item in items])}
        result = [
            RecommendationRead.model_validate(titles[item.title_id]).model_copy(
                update={"reason": item.reason, "score": round(item.score, 4)}
            )
            for item in items
            if item.title_id in titles
        ]
        return mark_favorites(result, self.favorites, user.id if user else None)
