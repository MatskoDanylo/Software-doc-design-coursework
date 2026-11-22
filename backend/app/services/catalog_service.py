from collections.abc import Sequence
from typing import Protocol

from app.core.errors import NotFoundError
from app.models import Genre, Title
from app.patterns.title_query_builder import TitleQuery, TitleQueryBuilder
from app.schemas.catalog import TitleFilters, TitlePage, TitleRead


class TitleReader(Protocol):
    def search(self, query: TitleQuery) -> tuple[Sequence[Title], int]: ...

    def get_detailed(self, title_id: int) -> Title | None: ...

    def list_countries(self) -> list[str]: ...


class GenreReader(Protocol):
    def list_all(self) -> Sequence[Genre]: ...


class CatalogService:
    def __init__(self, titles: TitleReader, genres: GenreReader) -> None:
        self.titles = titles
        self.genres = genres

    @staticmethod
    def build_query(filters: TitleFilters) -> TitleQuery:
        return (
            TitleQueryBuilder()
            .with_text(filters.q)
            .with_genres(filters.genre)
            .with_year_range(filters.year_from, filters.year_to)
            .with_country(filters.country)
            .with_kind(filters.kind)
            .with_min_rating(filters.min_rating)
            .sort_by(filters.sort, filters.order)
            .paginate(filters.page, filters.page_size)
            .build()
        )

    def search(self, filters: TitleFilters) -> TitlePage:
        query = self.build_query(filters)
        items, total = self.titles.search(query)
        return TitlePage(
            items=[TitleRead.model_validate(t) for t in items],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    def get_title(self, title_id: int) -> Title:
        title = self.titles.get_detailed(title_id)
        if title is None:
            raise NotFoundError("Title not found", code="title_not_found")
        return title

    def list_genres(self) -> Sequence[Genre]:
        return self.genres.list_all()

    def list_countries(self) -> list[str]:
        return self.titles.list_countries()
