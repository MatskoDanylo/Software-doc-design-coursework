from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from sqlalchemy import ColumnElement, Select, func, or_, select

from app.core.errors import UnprocessableError
from app.models import Title, TitleKind, WatchHistory, title_genres


class SortField(StrEnum):
    RATING = "rating"
    YEAR = "year"
    NAME = "name"
    POPULARITY = "popularity"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


DEFAULT_ORDER: dict[SortField, SortOrder] = {
    SortField.RATING: SortOrder.DESC,
    SortField.YEAR: SortOrder.DESC,
    SortField.NAME: SortOrder.ASC,
    SortField.POPULARITY: SortOrder.DESC,
}


@dataclass(frozen=True)
class TitleQuery:
    items: Select[tuple[Title]]
    count: Select[tuple[int]]
    page: int
    page_size: int


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _popularity() -> ColumnElement[int]:
    return (
        select(func.count(WatchHistory.id))
        .where(WatchHistory.title_id == Title.id)
        .correlate(Title)
        .scalar_subquery()
    )


class TitleQueryBuilder:
    MAX_PAGE_SIZE = 50
    DEFAULT_PAGE_SIZE = 20
    MIN_RATING, MAX_RATING = 0.0, 10.0

    def __init__(self) -> None:
        self._conditions: list[ColumnElement[bool]] = []
        self._order: list[ColumnElement[object]] = []
        self._page = 1
        self._page_size = self.DEFAULT_PAGE_SIZE

    def with_text(self, text: str | None) -> Self:
        if text is None or not text.strip():
            return self
        pattern = f"%{_escape_like(text.strip())}%"
        self._conditions.append(
            or_(Title.name.ilike(pattern, escape="\\"), Title.description.ilike(pattern, escape="\\"))
        )
        return self

    def with_genres(self, genre_ids: Iterable[int] | None) -> Self:
        ids = sorted(set(genre_ids or ()))
        if not ids:
            return self
        tagged = select(title_genres.c.title_id).where(title_genres.c.genre_id.in_(ids))
        self._conditions.append(Title.id.in_(tagged))
        return self

    def with_year_range(self, year_from: int | None = None, year_to: int | None = None) -> Self:
        if year_from is not None and year_to is not None and year_from > year_to:
            raise UnprocessableError("year_from must not be greater than year_to", code="invalid_query")
        if year_from is not None:
            self._conditions.append(Title.year >= year_from)
        if year_to is not None:
            self._conditions.append(Title.year <= year_to)
        return self

    def with_country(self, country: str | None) -> Self:
        if country is None or not country.strip():
            return self
        self._conditions.append(func.lower(Title.country) == country.strip().lower())
        return self

    def with_kind(self, kind: TitleKind | None) -> Self:
        if kind is not None:
            self._conditions.append(Title.kind == TitleKind(kind).value)
        return self

    def with_min_rating(self, min_rating: float | None) -> Self:
        if min_rating is None:
            return self
        if not self.MIN_RATING <= min_rating <= self.MAX_RATING:
            raise UnprocessableError(
                f"min_rating must be between {self.MIN_RATING} and {self.MAX_RATING}", code="invalid_query"
            )
        self._conditions.append(Title.rating >= min_rating)
        return self

    def sort_by(self, field: SortField | None, order: SortOrder | None = None) -> Self:
        if field is None:
            return self
        field = SortField(field)
        column: ColumnElement[object] = {
            SortField.RATING: Title.rating,
            SortField.YEAR: Title.year,
            SortField.NAME: func.lower(Title.name),
            SortField.POPULARITY: _popularity(),
        }[field]
        direction = SortOrder(order) if order is not None else DEFAULT_ORDER[field]
        self._order = [column.asc() if direction is SortOrder.ASC else column.desc()]
        return self

    def paginate(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Self:
        if page < 1:
            raise UnprocessableError("page must be >= 1", code="invalid_query")
        if not 1 <= page_size <= self.MAX_PAGE_SIZE:
            raise UnprocessableError(f"page_size must be between 1 and {self.MAX_PAGE_SIZE}", code="invalid_query")
        self._page, self._page_size = page, page_size
        return self

    def build(self) -> TitleQuery:
        items = (
            select(Title)
            .where(*self._conditions)
            .order_by(*self._order, Title.id.asc())
            .limit(self._page_size)
            .offset((self._page - 1) * self._page_size)
        )
        count = select(func.count()).select_from(Title).where(*self._conditions)
        return TitleQuery(items=items, count=count, page=self._page, page_size=self._page_size)
