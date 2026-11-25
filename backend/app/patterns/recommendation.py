from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import ClassVar, Protocol

from app.core.errors import UnprocessableError


@dataclass(frozen=True)
class RecommendationContext:
    user_id: int | None = None
    watched: frozenset[int] = frozenset()
    finished: frozenset[int] = frozenset()
    favorites: frozenset[int] = frozenset()
    seed_title_id: int | None = None

    @property
    def has_taste(self) -> bool:
        return bool(self.watched or self.favorites)


@dataclass(frozen=True)
class ScoredTitle:
    title_id: int
    score: float
    reason: str


@dataclass(frozen=True)
class TitleFeatures:
    id: int
    name: str
    year: int
    country: str
    rating: float
    genre_ids: frozenset[int]


@dataclass(frozen=True)
class PopularTitle:
    title_id: int
    window_viewers: int
    window_completions: int
    total_viewers: int
    total_completions: int
    rating: float


@dataclass(frozen=True)
class RecommendationConfig:
    default_strategy: str
    hybrid_weights: Mapping[str, float]
    popularity_window_days: int


DEFAULT_RECOMMENDATION_CONFIG = RecommendationConfig(
    default_strategy="hybrid",
    hybrid_weights={"genre_affinity": 0.5, "similar": 0.3, "popularity": 0.2},
    popularity_window_days=7,
)


class RecommendationSource(Protocol):
    def popular(self, since: datetime, exclude: Collection[int], limit: int) -> Sequence[PopularTitle]: ...

    def features(self, title_ids: Collection[int]) -> Mapping[int, TitleFeatures]: ...

    def candidates(self, genre_ids: Collection[int], exclude: Collection[int], limit: int) -> Sequence[TitleFeatures]: ...

    def similar_candidates(
        self, seed: TitleFeatures, exclude: Collection[int], limit: int
    ) -> Sequence[TitleFeatures]: ...

    def genre_names(self, genre_ids: Collection[int]) -> Mapping[int, str]: ...


def top_scored(items: Iterable[ScoredTitle], limit: int) -> list[ScoredTitle]:
    return sorted(items, key=lambda item: (-item.score, item.title_id))[:max(limit, 0)]


class RecommendationStrategy(ABC):
    code: ClassVar[str]

    @abstractmethod
    def recommend(self, context: RecommendationContext, limit: int) -> list[ScoredTitle]: ...


def _days(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} день"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} дні"
    return f"{n} днів"


class PopularityStrategy(RecommendationStrategy):
    code = "popularity"
    ALL_TIME_REASON = "Популярне серед глядачів"
    RATING_REASON = "Високий рейтинг"

    def __init__(self, source: RecommendationSource, window_days: int, clock: Callable[[], datetime]) -> None:
        self.source = source
        self.window_days = window_days
        self.clock = clock

    @property
    def window_reason(self) -> str:
        if self.window_days == 7:
            return "Популярне цього тижня"
        return f"Популярне за останні {_days(self.window_days)}"

    def recommend(self, context: RecommendationContext, limit: int) -> list[ScoredTitle]:
        if limit < 1:
            return []
        since = self.clock() - timedelta(days=self.window_days)
        rows = [r for r in self.source.popular(since, context.watched, limit) if r.title_id not in context.watched]
        rows = sorted(rows, key=self._rank)[:limit]
        return [
            ScoredTitle(row.title_id, 1 - index / len(rows), self._reason(row))
            for index, row in enumerate(rows)
        ]

    @staticmethod
    def _rank(row: PopularTitle) -> tuple[int, int, int, int, int, float, int]:
        tier = 0 if row.window_viewers > 0 else 1 if row.total_viewers > 0 else 2
        return (tier, -row.window_viewers, -row.window_completions, -row.total_viewers, -row.total_completions,
                -row.rating, row.title_id)

    def _reason(self, row: PopularTitle) -> str:
        if row.window_viewers > 0:
            return self.window_reason
        return self.ALL_TIME_REASON if row.total_viewers > 0 else self.RATING_REASON


@dataclass(frozen=True)
class GenreWeights:
    weights: Mapping[int, float]
    watched_genres: frozenset[int] = field(default_factory=frozenset)


class GenreAffinityStrategy(RecommendationStrategy):
    code = "genre_affinity"
    FINISHED_WEIGHT = 2.0
    STARTED_WEIGHT = 1.0
    FAVORITE_WEIGHT = 1.5
    AFFINITY_SHARE = 0.8
    RATING_SHARE = 0.2
    CANDIDATE_POOL = 200

    def __init__(self, source: RecommendationSource) -> None:
        self.source = source

    def genre_weights(self, context: RecommendationContext) -> GenreWeights:
        title_weights: dict[int, float] = defaultdict(float)
        for title_id in context.watched:
            title_weights[title_id] += self.FINISHED_WEIGHT if title_id in context.finished else self.STARTED_WEIGHT
        for title_id in context.favorites:
            title_weights[title_id] += self.FAVORITE_WEIGHT
        features = self.source.features(title_weights.keys())
        raw: dict[int, float] = defaultdict(float)
        watched_genres: set[int] = set()
        for title_id, weight in title_weights.items():
            title = features.get(title_id)
            if title is None:
                continue
            for genre_id in title.genre_ids:
                raw[genre_id] += weight
            if title_id in context.watched:
                watched_genres |= title.genre_ids
        total = sum(raw.values())
        if not total:
            return GenreWeights({})
        return GenreWeights({g: w / total for g, w in raw.items()}, frozenset(watched_genres))

    def recommend(self, context: RecommendationContext, limit: int) -> list[ScoredTitle]:
        taste = self.genre_weights(context)
        if not taste.weights or limit < 1:
            return []
        weights = taste.weights
        exclude = context.watched | context.favorites
        names = self.source.genre_names(weights.keys())
        scored = []
        for candidate in self.source.candidates(weights.keys(), exclude, self.CANDIDATE_POOL):
            shared = candidate.genre_ids & weights.keys()
            if candidate.id in exclude or not shared:
                continue
            affinity = sum(weights[g] for g in shared)
            top_genre = max(shared, key=lambda g: (weights[g], -g))
            scored.append(ScoredTitle(
                candidate.id,
                self.AFFINITY_SHARE * affinity + self.RATING_SHARE * candidate.rating / 10,
                self._reason(names.get(top_genre, ""), top_genre in taste.watched_genres),
            ))
        return top_scored(scored, limit)

    @staticmethod
    def _reason(genre: str, watched: bool) -> str:
        return f"Бо ви дивились жанр «{genre}»" if watched else f"Бо у вашому Вибраному є жанр «{genre}»"


class SimilarTitlesStrategy(RecommendationStrategy):
    code = "similar"
    GENRE_SHARE = 0.6
    YEAR_SHARE = 0.25
    COUNTRY_SHARE = 0.15
    YEAR_SPAN = 15
    CANDIDATE_POOL = 200

    def __init__(self, source: RecommendationSource) -> None:
        self.source = source

    @classmethod
    def similarity(cls, seed: TitleFeatures, other: TitleFeatures) -> float:
        union = seed.genre_ids | other.genre_ids
        genres = len(seed.genre_ids & other.genre_ids) / len(union) if union else 0.0
        years = max(0.0, 1 - abs(seed.year - other.year) / cls.YEAR_SPAN)
        country = float(seed.country.casefold() == other.country.casefold())
        return cls.GENRE_SHARE * genres + cls.YEAR_SHARE * years + cls.COUNTRY_SHARE * country

    def recommend(self, context: RecommendationContext, limit: int) -> list[ScoredTitle]:
        seed_id = context.seed_title_id
        seed = None if seed_id is None else self.source.features([seed_id]).get(seed_id)
        if seed is None or limit < 1:
            return []
        exclude = context.watched | {seed.id}
        reason = f"Схоже на «{seed.name}»"
        scored = [
            ScoredTitle(candidate.id, self.similarity(seed, candidate), reason)
            for candidate in self.source.similar_candidates(seed, exclude, self.CANDIDATE_POOL)
            if candidate.id not in exclude
        ]
        return top_scored((s for s in scored if s.score > 0), limit)


class HybridStrategy(RecommendationStrategy):
    code = "hybrid"
    OVERFETCH = 3

    def __init__(self, components: Sequence[tuple[RecommendationStrategy, float]]) -> None:
        self.components = [(strategy, weight) for strategy, weight in components if weight > 0]

    def recommend(self, context: RecommendationContext, limit: int) -> list[ScoredTitle]:
        if limit < 1:
            return []
        totals: dict[int, float] = defaultdict(float)
        best: dict[int, tuple[float, str]] = {}
        for strategy, weight in self.components:
            items = strategy.recommend(context, limit * self.OVERFETCH)
            top = max((item.score for item in items), default=0.0)
            if top <= 0:
                continue
            for item in items:
                contribution = weight * item.score / top
                totals[item.title_id] += contribution
                if contribution > best.get(item.title_id, (-1.0, ""))[0]:
                    best[item.title_id] = (contribution, item.reason)
        return top_scored((ScoredTitle(t, score, best[t][1]) for t, score in totals.items()), limit)


class UnknownStrategyError(UnprocessableError):
    code = "unknown_strategy"


@dataclass(frozen=True)
class StrategyEnv:
    source: RecommendationSource
    config: RecommendationConfig
    clock: Callable[[], datetime]
    registry: "StrategyRegistry"

    def create(self, code: str) -> RecommendationStrategy:
        return self.registry.create(code, self)


type StrategyFactory = Callable[[StrategyEnv], RecommendationStrategy]


class StrategyRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, StrategyFactory] = {}

    def register(self, code: str, factory: StrategyFactory) -> None:
        self._factories[code] = factory

    def codes(self) -> tuple[str, ...]:
        return tuple(self._factories)

    def ensure_known(self, code: str) -> str:
        if code not in self._factories:
            raise UnknownStrategyError(
                f"Unknown recommendation strategy '{code}'; expected one of: {', '.join(self._factories)}"
            )
        return code

    def create(self, code: str, env: StrategyEnv) -> RecommendationStrategy:
        return self._factories[self.ensure_known(code)](env)


def _hybrid(env: StrategyEnv) -> HybridStrategy:
    return HybridStrategy([
        (env.create(code), weight)
        for code, weight in env.config.hybrid_weights.items()
        if code != HybridStrategy.code
    ])


def default_strategy_registry() -> StrategyRegistry:
    registry = StrategyRegistry()
    registry.register(
        PopularityStrategy.code,
        lambda env: PopularityStrategy(env.source, env.config.popularity_window_days, env.clock),
    )
    registry.register(GenreAffinityStrategy.code, lambda env: GenreAffinityStrategy(env.source))
    registry.register(SimilarTitlesStrategy.code, lambda env: SimilarTitlesStrategy(env.source))
    registry.register(HybridStrategy.code, _hybrid)
    return registry
