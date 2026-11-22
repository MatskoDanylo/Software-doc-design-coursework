from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import TitleKind
from app.patterns.title_query_builder import SortField, SortOrder, TitleQueryBuilder


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TitleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: TitleKind
    name: str
    description: str
    year: int
    country: str
    rating: float
    poster_url: str | None
    genres: list[GenreRead]


class EpisodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    name: str


class SeasonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    episodes: list[EpisodeRead]


class TitleDetail(TitleRead):
    seasons: list[SeasonRead]


class TitlePage(BaseModel):
    items: list[TitleRead]
    total: int
    page: int
    page_size: int


class TitleFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    q: str | None = Field(default=None, max_length=100)
    genre: list[int] = Field(default_factory=list, max_length=20)
    year_from: int | None = Field(default=None, ge=1880, le=2100)
    year_to: int | None = Field(default=None, ge=1880, le=2100)
    country: str | None = Field(default=None, max_length=100)
    kind: TitleKind | None = None
    min_rating: float | None = Field(default=None, ge=TitleQueryBuilder.MIN_RATING, le=TitleQueryBuilder.MAX_RATING)
    sort: SortField = SortField.RATING
    order: SortOrder | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=TitleQueryBuilder.DEFAULT_PAGE_SIZE, ge=1, le=TitleQueryBuilder.MAX_PAGE_SIZE)

    @model_validator(mode="after")
    def _check_year_range(self) -> "TitleFilters":
        if self.year_from is not None and self.year_to is not None and self.year_from > self.year_to:
            raise ValueError("year_from must not be greater than year_to")
        return self
