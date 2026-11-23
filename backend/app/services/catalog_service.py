from collections.abc import Sequence
from typing import Protocol

from app.core.errors import NotFoundError
from app.models import Genre, Title
from app.patterns.title_query_builder import TitleQuery, TitleQueryBuilder
from app.schemas.catalog import TitleDetail, TitleFilters, TitlePage, TitleRead
from app.services.favorite_service import mark_favorites
from app.services.ports import FavoriteReader


class TitleReader(Protocol):
    def search(self, query: TitleQuery) -> tuple[Sequence[Title], int]: ...

    def get_detailed(self, title_id: int) -> Title | None: ...

    def list_countries(self) -> list[str]: ...


class GenreReader(Protocol):
    def list_all(self) -> Sequence[Genre]: ...


class CatalogService:
    def __init__(self, titles: TitleReader, genres: GenreReader, favorites: FavoriteReader) -> None:
        self.titles = titles
        self.genres = genres
        self.favorites = favorites

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

    def search(self, filters: TitleFilters, viewer_id: int | None = None) -> TitlePage:
        query = self.build_query(filters)
        items, total = self.titles.search(query)
        return TitlePage(
            items=mark_favorites([TitleRead.model_validate(t) for t in items], self.favorites, viewer_id),
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    def get_title(self, title_id: int, viewer_id: int | None = None) -> TitleDetail:
        title = self.titles.get_detailed(title_id)
        if title is None:
            raise NotFoundError("Title not found", code="title_not_found")
        return mark_favorites([TitleDetail.model_validate(title)], self.favorites, viewer_id)[0]

    def list_genres(self) -> Sequence[Genre]:
        return self.genres.list_all()

    def list_countries(self) -> list[str]:
        return self.titles.list_countries()
