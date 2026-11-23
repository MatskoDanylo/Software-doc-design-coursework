from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.errors import UnprocessableError
from app.models import Genre, TitleKind
from app.patterns.title_query_builder import SortField, SortOrder, TitleQueryBuilder
from tests.factories import add_season, add_views, make_genre, make_title, make_user

ALL = ["The Matrix", "Amelie", "Dark", "Inception", "100% Love", "Taxi"]


@pytest.fixture
def session() -> Iterator[Session]:
    with SessionLocal() as session:
        drama, comedy, scifi = (make_genre(session, n) for n in ("Drama", "Comedy", "Sci-Fi"))
        make_title(session, "The Matrix", [scifi], year=1999, rating=8.7,
                   description="A hacker learns the truth about reality")
        make_title(session, "Amelie", [comedy, drama], year=2001, country="France", rating=8.3,
                   description="A shy waitress decides to change lives")
        make_title(session, "Dark", [scifi, drama], kind=TitleKind.SERIES.value, year=2017, country="Germany",
                   rating=8.7, description="Time travel mystery in a small town")
        make_title(session, "Inception", [scifi], year=2010, rating=8.8, description="Dreams within dreams")
        make_title(session, "100% Love", [comedy], year=2011, country="India", rating=5.5)
        make_title(session, "Taxi", [comedy], year=1998, country="France", rating=7.0)
        yield session
        session.rollback()


def names(session: Session, builder: TitleQueryBuilder) -> list[str]:
    return [t.name for t in session.scalars(builder.build().items)]


def total(session: Session, builder: TitleQueryBuilder) -> int:
    return session.scalar(builder.build().count)


def genre_id(session: Session, name: str) -> int:
    return session.scalar(select(Genre.id).where(Genre.name == name))


def test_without_filters_returns_everything_in_insertion_order(session: Session) -> None:
    builder = TitleQueryBuilder()

    assert names(session, builder) == ALL
    assert total(session, builder) == len(ALL)


def test_unset_parameters_are_ignored(session: Session) -> None:
    builder = (
        TitleQueryBuilder()
        .with_text(None).with_text("   ")
        .with_genres(None).with_genres([])
        .with_year_range()
        .with_country(None).with_country("")
        .with_kind(None)
        .with_min_rating(None)
        .sort_by(None)
    )

    assert names(session, builder) == ALL


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("matrix", ["The Matrix"]),
        ("TIME TRAVEL", ["Dark"]),
        ("dream", ["Inception"]),
        ("  a shy  ", ["Amelie"]),
        ("100%", ["100% Love"]),
        ("%", ["100% Love"]),
        ("_", []),
        ("nothing like this", []),
    ],
)
def test_with_text_searches_name_and_description(session: Session, text: str, expected: list[str]) -> None:
    assert names(session, TitleQueryBuilder().with_text(text)) == expected


@pytest.mark.parametrize(
    ("genres", "expected"),
    [
        (["Comedy"], ["Amelie", "100% Love", "Taxi"]),
        (["Drama", "Comedy"], ["Amelie", "Dark", "100% Love", "Taxi"]),
        (["Sci-Fi", "Sci-Fi"], ["The Matrix", "Dark", "Inception"]),
    ],
)
def test_with_genres_matches_any_of_given_without_duplicates(
    session: Session, genres: list[str], expected: list[str]
) -> None:
    builder = TitleQueryBuilder().with_genres([genre_id(session, g) for g in genres])

    assert names(session, builder) == expected
    assert total(session, builder) == len(expected)


def test_with_genres_unknown_id_matches_nothing(session: Session) -> None:
    assert names(session, TitleQueryBuilder().with_genres([999_999])) == []


@pytest.mark.parametrize(
    ("year_from", "year_to", "expected"),
    [
        (2010, None, ["Dark", "Inception", "100% Love"]),
        (None, 1999, ["The Matrix", "Taxi"]),
        (1999, 2001, ["The Matrix", "Amelie"]),
        (2010, 2010, ["Inception"]),
    ],
)
def test_with_year_range(session: Session, year_from: int | None, year_to: int | None, expected: list[str]) -> None:
    assert names(session, TitleQueryBuilder().with_year_range(year_from, year_to)) == expected


def test_with_year_range_rejects_inverted_bounds() -> None:
    with pytest.raises(UnprocessableError):
        TitleQueryBuilder().with_year_range(2020, 2000)


@pytest.mark.parametrize("country", ["France", "france", " FRANCE "])
def test_with_country_is_case_insensitive_exact_match(session: Session, country: str) -> None:
    assert names(session, TitleQueryBuilder().with_country(country)) == ["Amelie", "Taxi"]


def test_with_country_does_not_match_partially(session: Session) -> None:
    assert names(session, TitleQueryBuilder().with_country("Fra")) == []


@pytest.mark.parametrize(
    ("kind", "expected"),
    [(TitleKind.SERIES, ["Dark"]), (TitleKind.MOVIE, ["The Matrix", "Amelie", "Inception", "100% Love", "Taxi"])],
)
def test_with_kind(session: Session, kind: TitleKind, expected: list[str]) -> None:
    assert names(session, TitleQueryBuilder().with_kind(kind)) == expected


def test_with_min_rating_is_inclusive(session: Session) -> None:
    assert names(session, TitleQueryBuilder().with_min_rating(8.7)) == ["The Matrix", "Dark", "Inception"]


@pytest.mark.parametrize("rating", [-0.1, 10.1])
def test_with_min_rating_rejects_out_of_range(rating: float) -> None:
    with pytest.raises(UnprocessableError):
        TitleQueryBuilder().with_min_rating(rating)


@pytest.mark.parametrize(
    ("field", "order", "expected"),
    [
        (SortField.RATING, None, ["Inception", "The Matrix", "Dark", "Amelie", "Taxi", "100% Love"]),
        (SortField.RATING, SortOrder.ASC, ["100% Love", "Taxi", "Amelie", "The Matrix", "Dark", "Inception"]),
        (SortField.YEAR, None, ["Dark", "100% Love", "Inception", "Amelie", "The Matrix", "Taxi"]),
        (SortField.YEAR, SortOrder.ASC, ["Taxi", "The Matrix", "Amelie", "Inception", "100% Love", "Dark"]),
        (SortField.NAME, None, ["100% Love", "Amelie", "Dark", "Inception", "Taxi", "The Matrix"]),
        (SortField.NAME, SortOrder.DESC, ["The Matrix", "Taxi", "Inception", "Dark", "Amelie", "100% Love"]),
    ],
)
def test_sort_by(session: Session, field: SortField, order: SortOrder | None, expected: list[str]) -> None:
    assert names(session, TitleQueryBuilder().sort_by(field, order)) == expected


def test_sort_by_popularity_counts_distinct_viewers(session: Session) -> None:
    first, second, third = (make_user(session, f"viewer{i}@example.com") for i in range(3))
    titles = {t.name: t for t in session.scalars(TitleQueryBuilder().build().items)}
    add_views(session, titles["Taxi"], [first.id, second.id])
    for episode in add_season(session, titles["Dark"], 1, ["One", "Two", "Three"]).episodes:
        add_views(session, titles["Dark"], [third.id], episode)

    assert names(session, TitleQueryBuilder().sort_by(SortField.POPULARITY))[:3] == ["Taxi", "Dark", "The Matrix"]


def test_last_sort_by_wins(session: Session) -> None:
    builder = TitleQueryBuilder().sort_by(SortField.RATING).sort_by(SortField.NAME)

    assert names(session, builder)[0] == "100% Love"


def test_paginate_limits_items_but_not_total(session: Session) -> None:
    builder = TitleQueryBuilder().sort_by(SortField.NAME).paginate(page=2, page_size=4)
    query = builder.build()

    assert names(session, builder) == ["Taxi", "The Matrix"]
    assert total(session, builder) == len(ALL)
    assert (query.page, query.page_size) == (2, 4)


def test_paginate_beyond_last_page_is_empty(session: Session) -> None:
    assert names(session, TitleQueryBuilder().paginate(page=5, page_size=10)) == []


def test_default_page_size() -> None:
    query = TitleQueryBuilder().build()

    assert (query.page, query.page_size) == (1, TitleQueryBuilder.DEFAULT_PAGE_SIZE)


@pytest.mark.parametrize(("page", "page_size"), [(0, 10), (1, 0), (1, TitleQueryBuilder.MAX_PAGE_SIZE + 1)])
def test_paginate_validates_bounds(page: int, page_size: int) -> None:
    with pytest.raises(UnprocessableError):
        TitleQueryBuilder().paginate(page, page_size)


def test_combined_filters(session: Session) -> None:
    builder = (
        TitleQueryBuilder()
        .with_genres([genre_id(session, "Sci-Fi")])
        .with_country("USA")
        .with_year_range(year_from=1990)
        .with_kind(TitleKind.MOVIE)
        .sort_by(SortField.YEAR)
    )

    assert names(session, builder) == ["Inception", "The Matrix"]
    assert total(session, builder) == 2


def test_combined_filters_with_text_rating_and_pagination(session: Session) -> None:
    builder = (
        TitleQueryBuilder()
        .with_text("a")
        .with_genres([genre_id(session, "Drama"), genre_id(session, "Comedy")])
        .with_min_rating(7.0)
        .sort_by(SortField.RATING, SortOrder.ASC)
        .paginate(page=1, page_size=2)
    )

    assert names(session, builder) == ["Taxi", "Amelie"]
    assert total(session, builder) == 3
