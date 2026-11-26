from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TitleKind

Name = Annotated[str, Field(min_length=1, max_length=255)]
GenreName = Annotated[str, Field(min_length=1, max_length=80)]
Description = Annotated[str, Field(max_length=5000)]
Year = Annotated[int, Field(ge=1880, le=2100)]
Country = Annotated[str, Field(min_length=1, max_length=100)]
Rating = Annotated[float, Field(ge=0, le=10)]
GenreIds = Annotated[list[int], Field(max_length=20)]
SeasonNumber = Annotated[int, Field(ge=1, le=100)]
EpisodeNumber = Annotated[int, Field(ge=1, le=1000)]


class _Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _PartialPayload(_Payload):
    @field_validator("*", mode="before")
    @classmethod
    def _not_null(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class TitleCreate(_Payload):
    kind: TitleKind
    name: Name
    description: Description = ""
    year: Year
    country: Country
    rating: Rating = 0.0
    genre_ids: GenreIds = []


class TitleUpdate(_PartialPayload):
    kind: TitleKind | None = None
    name: Name | None = None
    description: Description | None = None
    year: Year | None = None
    country: Country | None = None
    rating: Rating | None = None
    genre_ids: GenreIds | None = None


class GenreWrite(_Payload):
    name: GenreName


class SeasonCreate(_Payload):
    number: SeasonNumber


class SeasonUpdate(_PartialPayload):
    number: SeasonNumber | None = None


class EpisodeCreate(_Payload):
    number: EpisodeNumber
    name: Name


class EpisodeUpdate(_PartialPayload):
    number: EpisodeNumber | None = None
    name: Name | None = None
