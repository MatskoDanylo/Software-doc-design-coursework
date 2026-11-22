from collections.abc import Sequence
from typing import Protocol

from app.models import Episode, Genre, Season, Title, TitleKind


class EntityStore[T](Protocol):
    def get(self, entity_id: int) -> T | None: ...

    def add(self, entity: T) -> T: ...

    def delete(self, entity: T) -> None: ...


class TitleStore(EntityStore[Title], Protocol):
    def get_by_identity(self, kind: TitleKind, name: str, year: int) -> Title | None: ...


class GenreStore(EntityStore[Genre], Protocol):
    def get_by_name(self, name: str) -> Genre | None: ...

    def get_many(self, genre_ids: Sequence[int]) -> Sequence[Genre]: ...


class SeasonStore(EntityStore[Season], Protocol):
    def get_by_number(self, title_id: int, number: int) -> Season | None: ...


class EpisodeStore(EntityStore[Episode], Protocol):
    def get_by_number(self, season_id: int, number: int) -> Episode | None: ...
