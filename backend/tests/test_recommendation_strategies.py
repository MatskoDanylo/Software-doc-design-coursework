from collections.abc import Collection, Mapping, Sequence
from datetime import UTC, datetime, timedelta

import pytest

from app.patterns.recommendation import (
    DEFAULT_RECOMMENDATION_CONFIG,
    GenreAffinityStrategy,
    HybridStrategy,
    PopularityStrategy,
    PopularTitle,
    RecommendationConfig,
    RecommendationContext,
    RecommendationStrategy,
    ScoredTitle,
    SimilarTitlesStrategy,
    StrategyEnv,
    TitleFeatures,
    UnknownStrategyError,
    default_strategy_registry,
)

NOW = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
DRAMA, COMEDY, SCIFI, HORROR = 1, 2, 3, 4
GENRES = {DRAMA: "Драма", COMEDY: "Комедія", SCIFI: "Фантастика", HORROR: "Жахи"}


def title(id: int, *genres: int, year: int = 2000, country: str = "США", rating: float = 5.0) -> TitleFeatures:
    return TitleFeatures(id=id, name=f"T{id}", year=year, country=country, rating=rating, genre_ids=frozenset(genres))


def popular(id: int, wv: int = 0, wc: int = 0, tv: int = 0, tc: int = 0, rating: float = 5.0) -> PopularTitle:
    return PopularTitle(id, wv, wc, tv, tc, rating)


class FakeSource:
    def __init__(self, titles: Sequence[TitleFeatures] = (), popular: Sequence[PopularTitle] = ()) -> None:
        self.titles = {t.id: t for t in titles}
        self._popular = list(popular)
        self.since: datetime | None = None

    def popular(self, since: datetime, exclude: Collection[int], limit: int) -> Sequence[PopularTitle]:
        self.since = since
        return [p for p in self._popular if p.title_id not in exclude]

    def features(self, title_ids: Collection[int]) -> Mapping[int, TitleFeatures]:
        return {i: self.titles[i] for i in title_ids if i in self.titles}

    def candidates(self, genre_ids: Collection[int], exclude: Collection[int], limit: int) -> Sequence[TitleFeatures]:
        return [t for t in self.titles.values() if t.genre_ids & set(genre_ids) and t.id not in exclude][:limit]

    def similar_candidates(self, seed: TitleFeatures, exclude: Collection[int], limit: int) -> Sequence[TitleFeatures]:
        return [
            t
            for t in self.titles.values()
            if (t.genre_ids & seed.genre_ids or t.country == seed.country) and t.id not in exclude
        ][:limit]

    def genre_names(self, genre_ids: Collection[int]) -> Mapping[int, str]:
        return {g: GENRES[g] for g in genre_ids}


class StubStrategy(RecommendationStrategy):
    code = "stub"

    def __init__(self, *items: ScoredTitle) -> None:
        self.items = list(items)
        self.limits: list[int] = []

    def recommend(self, context: RecommendationContext, limit: int) -> list[ScoredTitle]:
        self.limits.append(limit)
        return self.items[:limit]


def ids(items: Sequence[ScoredTitle]) -> list[int]:
    return [i.title_id for i in items]


def ctx(
    watched: Collection[int] = (),
    finished: Collection[int] = (),
    favorites: Collection[int] = (),
    seed: int | None = None,
) -> RecommendationContext:
    return RecommendationContext(
        user_id=1,
        watched=frozenset(watched),
        finished=frozenset(finished),
        favorites=frozenset(favorites),
        seed_title_id=seed,
    )


class TestPopularity:
    def strategy(self, *rows: PopularTitle, window_days: int = 7) -> tuple[PopularityStrategy, FakeSource]:
        source = FakeSource(popular=rows)
        return PopularityStrategy(source, window_days, lambda: NOW), source

    def test_orders_window_viewers_then_completions_then_all_time_stats_then_rating(self) -> None:
        strategy, source = self.strategy(
            popular(1, rating=9.9),
            popular(2, tv=50, tc=80),
            popular(3, wv=2, wc=1, tv=3),
            popular(4, wv=2, wc=5, tv=3),
            popular(5, wv=7),
            popular(6, tv=60),
            popular(7, wv=2, wc=5, tv=9),
            popular(8, rating=3.0),
        )

        items = strategy.recommend(RecommendationContext(), 10)

        assert ids(items) == [5, 7, 4, 3, 6, 2, 1, 8]
        assert source.since == NOW - timedelta(days=7)
        assert [i.score for i in items] == sorted((i.score for i in items), reverse=True)
        assert items[0].score == 1.0

    def test_reasons_follow_the_tier(self) -> None:
        strategy, _ = self.strategy(popular(1, wv=1), popular(2, tv=4), popular(3))

        reasons = [i.reason for i in strategy.recommend(RecommendationContext(), 3)]

        assert reasons == ["Популярне цього тижня", "Популярне серед глядачів", "Високий рейтинг"]

    @pytest.mark.parametrize(
        ("days", "reason"),
        [
            (7, "Популярне цього тижня"),
            (1, "Популярне за останні 1 день"),
            (3, "Популярне за останні 3 дні"),
            (30, "Популярне за останні 30 днів"),
            (21, "Популярне за останні 21 день"),
            (12, "Популярне за останні 12 днів"),
        ],
    )
    def test_window_reason_uses_configured_days(self, days: int, reason: str) -> None:
        strategy, source = self.strategy(popular(1, wv=1), window_days=days)

        assert strategy.recommend(RecommendationContext(), 1)[0].reason == reason
        assert source.since == NOW - timedelta(days=days)

    def test_excludes_watched_titles_and_respects_limit(self) -> None:
        strategy, _ = self.strategy(popular(1, wv=9), popular(2, wv=5), popular(3, wv=3), popular(4, wv=1))

        assert ids(strategy.recommend(ctx(watched=[1]), 2)) == [2, 3]
        assert strategy.recommend(ctx(), 0) == []


class TestGenreAffinity:
    def test_weights_are_normalized_and_finished_titles_weigh_more(self) -> None:
        source = FakeSource([title(1, DRAMA), title(2, COMEDY), title(3, SCIFI)])

        taste = GenreAffinityStrategy(source).genre_weights(ctx(watched=[1, 2], finished=[1], favorites=[3]))

        total = 2.0 + 1.0 + 1.5
        assert taste.weights == pytest.approx({DRAMA: 2.0 / total, COMEDY: 1.0 / total, SCIFI: 1.5 / total})
        assert sum(taste.weights.values()) == pytest.approx(1.0)
        assert taste.watched_genres == {DRAMA, COMEDY}

    def test_prefers_genres_of_finished_titles_over_rating(self) -> None:
        source = FakeSource(
            [
                title(1, DRAMA),
                title(2, COMEDY),
                title(10, DRAMA, rating=5.0),
                title(11, COMEDY, rating=9.0),
                title(12, HORROR, rating=10.0),
            ]
        )

        items = GenreAffinityStrategy(source).recommend(ctx(watched=[1, 2], finished=[1]), 5)

        assert ids(items) == [10, 11]
        assert items[0].score == pytest.approx(0.8 * 2 / 3 + 0.2 * 0.5)
        assert items[0].reason == "Бо ви дивились жанр «Драма»"

    def test_rating_breaks_ties_within_a_genre(self) -> None:
        source = FakeSource([title(1, DRAMA), title(10, DRAMA, rating=6.0), title(11, DRAMA, rating=8.0)])

        assert ids(GenreAffinityStrategy(source).recommend(ctx(watched=[1]), 5)) == [11, 10]

    def test_matching_more_liked_genres_scores_higher(self) -> None:
        source = FakeSource([title(1, DRAMA, SCIFI), title(10, DRAMA), title(11, DRAMA, SCIFI)])

        assert ids(GenreAffinityStrategy(source).recommend(ctx(watched=[1]), 5)) == [11, 10]

    def test_excludes_watched_and_favorite_titles(self) -> None:
        source = FakeSource([title(1, DRAMA), title(2, DRAMA), title(3, DRAMA), title(4, DRAMA)])

        assert ids(GenreAffinityStrategy(source).recommend(ctx(watched=[1, 2], favorites=[3]), 5)) == [4]

    def test_favorite_only_genre_gets_its_own_reason(self) -> None:
        source = FakeSource([title(1, HORROR), title(10, HORROR)])

        [item] = GenreAffinityStrategy(source).recommend(ctx(favorites=[1]), 5)

        assert item.reason == "Бо у вашому Вибраному є жанр «Жахи»"

    def test_no_taste_means_no_recommendations(self) -> None:
        assert GenreAffinityStrategy(FakeSource([title(10, DRAMA)])).recommend(ctx(), 5) == []

    def test_titles_removed_from_catalog_do_not_shape_taste(self) -> None:
        source = FakeSource([title(1, DRAMA), title(10, DRAMA), title(11, COMEDY)])

        strategy = GenreAffinityStrategy(source)

        assert strategy.genre_weights(ctx(watched=[1, 99], finished=[99])).weights == {DRAMA: 1.0}
        assert strategy.recommend(ctx(watched=[99]), 5) == []

    def test_never_returns_excluded_titles_even_if_source_does(self) -> None:
        class LeakySource(FakeSource):
            def candidates(
                self, genre_ids: Collection[int], exclude: Collection[int], limit: int
            ) -> Sequence[TitleFeatures]:
                return list(self.titles.values())

        source = LeakySource([title(1, DRAMA), title(2, DRAMA), title(3, HORROR)])

        assert ids(GenreAffinityStrategy(source).recommend(ctx(watched=[1]), 5)) == [2]


class TestSimilar:
    def test_without_seed_returns_nothing(self) -> None:
        assert SimilarTitlesStrategy(FakeSource([title(1, DRAMA), title(2, DRAMA)])).recommend(ctx(), 5) == []

    def test_unknown_seed_returns_nothing(self) -> None:
        assert SimilarTitlesStrategy(FakeSource([title(1, DRAMA)])).recommend(ctx(seed=99), 5) == []

    def test_ranks_by_shared_genres_close_year_and_country(self) -> None:
        seed = title(1, DRAMA, SCIFI, year=2010, country="США")
        source = FakeSource(
            [
                seed,
                title(2, DRAMA, SCIFI, year=2010, country="США"),
                title(3, DRAMA, SCIFI, year=1990, country="Франція"),
                title(4, DRAMA, year=2011, country="США"),
                title(5, COMEDY, year=2010, country="США"),
                title(6, HORROR, year=1950, country="Японія"),
            ]
        )

        items = SimilarTitlesStrategy(source).recommend(ctx(seed=1), 10)

        assert ids(items) == [2, 4, 3, 5]
        assert [i.score for i in items] == pytest.approx([1.0, 0.6 * 0.5 + 0.25 * (1 - 1 / 15) + 0.15, 0.6, 0.4])
        assert {i.reason for i in items} == {"Схоже на «T1»"}

    def test_excludes_seed_and_watched_titles(self) -> None:
        source = FakeSource([title(1, DRAMA), title(2, DRAMA), title(3, DRAMA)])

        assert ids(SimilarTitlesStrategy(source).recommend(ctx(watched=[2], seed=1), 5)) == [3]


class TestHybrid:
    def test_merges_normalized_weighted_scores_and_deduplicates(self) -> None:
        genre = StubStrategy(ScoredTitle(1, 0.8, "genre"), ScoredTitle(2, 0.4, "genre"))
        popular_ = StubStrategy(ScoredTitle(2, 10.0, "popular"), ScoredTitle(3, 5.0, "popular"))

        items = HybridStrategy([(genre, 0.6), (popular_, 0.4)]).recommend(ctx(), 5)

        assert ids(items) == [2, 1, 3]
        scores = {i.title_id: i.score for i in items}
        assert scores == pytest.approx({1: 0.6, 2: 0.6 * 0.5 + 0.4, 3: 0.4 * 0.5})
        assert len(items) == len({i.title_id for i in items})

    def test_reason_comes_from_the_largest_contribution(self) -> None:
        genre = StubStrategy(ScoredTitle(1, 1.0, "genre"), ScoredTitle(2, 0.2, "genre"))
        popular_ = StubStrategy(ScoredTitle(2, 1.0, "popular"))

        reasons = {i.title_id: i.reason for i in HybridStrategy([(genre, 0.5), (popular_, 0.5)]).recommend(ctx(), 5)}

        assert reasons == {1: "genre", 2: "popular"}

    def test_overfetches_components_and_skips_zero_weights(self) -> None:
        used, unused = StubStrategy(ScoredTitle(1, 1.0, "a")), StubStrategy(ScoredTitle(2, 1.0, "b"))

        items = HybridStrategy([(used, 1.0), (unused, 0.0)]).recommend(ctx(), 4)

        assert ids(items) == [1]
        assert used.limits == [12] and unused.limits == []

    def test_component_without_positive_scores_does_not_distort_the_mix(self) -> None:
        empty, zero = StubStrategy(), StubStrategy(ScoredTitle(5, 0.0, "zero"))
        genre = StubStrategy(ScoredTitle(1, 0.5, "genre"), ScoredTitle(2, 0.25, "genre"))

        items = HybridStrategy([(empty, 0.5), (zero, 0.3), (genre, 0.2)]).recommend(ctx(), 5)

        assert ids(items) == [1, 2]
        assert [i.score for i in items] == pytest.approx([0.2, 0.1])

    def test_non_positive_limit_returns_nothing(self) -> None:
        stub = StubStrategy(ScoredTitle(1, 1.0, "a"))

        assert HybridStrategy([(stub, 1.0)]).recommend(ctx(), 0) == []
        assert stub.limits == []

    def test_composes_real_strategies_through_the_same_interface(self) -> None:
        source = FakeSource(
            [title(1, DRAMA), title(2, DRAMA, rating=9.0), title(3, COMEDY)],
            [popular(3, wv=10), popular(2, wv=1)],
        )
        hybrid = HybridStrategy(
            [
                (GenreAffinityStrategy(source), 0.5),
                (PopularityStrategy(source, 7, lambda: NOW), 0.5),
            ]
        )

        items = hybrid.recommend(ctx(watched=[1], finished=[1]), 5)

        assert ids(items) == [2, 3]
        assert 1 not in ids(items)


class TestRegistry:
    def env(self, config: RecommendationConfig = DEFAULT_RECOMMENDATION_CONFIG) -> StrategyEnv:
        return StrategyEnv(FakeSource(), config, lambda: NOW, default_strategy_registry())

    def test_registers_all_strategies(self) -> None:
        env = self.env()

        assert env.registry.codes() == ("popularity", "genre_affinity", "similar", "hybrid")
        assert isinstance(env.create("popularity"), PopularityStrategy)
        assert isinstance(env.create("genre_affinity"), GenreAffinityStrategy)
        assert isinstance(env.create("similar"), SimilarTitlesStrategy)

    def test_hybrid_is_assembled_from_configured_weights(self) -> None:
        config = RecommendationConfig("hybrid", {"popularity": 0.3, "similar": 0.0, "genre_affinity": 0.7}, 30)

        hybrid = self.env(config).create("hybrid")

        assert isinstance(hybrid, HybridStrategy)
        assert [(type(s), w) for s, w in hybrid.components] == [(PopularityStrategy, 0.3), (GenreAffinityStrategy, 0.7)]
        popularity = hybrid.components[0][0]
        assert isinstance(popularity, PopularityStrategy) and popularity.window_days == 30

    def test_unknown_strategy_is_unprocessable(self) -> None:
        with pytest.raises(UnknownStrategyError) as error:
            self.env().create("random")

        assert (error.value.status_code, error.value.code) == (422, "unknown_strategy")

    def test_new_strategy_is_added_without_touching_existing_code(self) -> None:
        env = self.env()
        stub = StubStrategy(ScoredTitle(1, 1.0, "new"))
        env.registry.register("editors_choice", lambda _: stub)

        assert env.create("editors_choice") is stub
        assert env.registry.codes()[-1] == "editors_choice"
