from collections.abc import Sequence

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.storage import FileStorage
from app.models import Episode, Genre, Season, Title, TitleKind
from app.schemas.admin_catalog import (
    EpisodeCreate,
    EpisodeUpdate,
    GenreWrite,
    SeasonCreate,
    SeasonUpdate,
    TitleCreate,
    TitleUpdate,
)
from app.schemas.catalog import EpisodeRead, GenreRead, SeasonRead, TitleDetail
from app.services.ports import EpisodeStore, GenreStore, SeasonStore, TitleStore


class AdminCatalogService:
    def __init__(
        self,
        titles: TitleStore,
        genres: GenreStore,
        seasons: SeasonStore,
        episodes: EpisodeStore,
        storage: FileStorage,
    ) -> None:
        self.titles = titles
        self.genres = genres
        self.seasons = seasons
        self.episodes = episodes
        self.storage = storage

    def create_title(self, data: TitleCreate) -> TitleDetail:
        self._ensure_title_unique(data.kind, data.name, data.year)
        title = Title(**data.model_dump(exclude={"genre_ids"}))
        title.genres = self._resolve_genres(data.genre_ids)
        return TitleDetail.model_validate(self.titles.add(title))

    def update_title(self, title_id: int, data: TitleUpdate) -> TitleDetail:
        title = self._get_title(title_id)
        changes = data.model_dump(exclude_unset=True, exclude={"genre_ids"})
        kind = TitleKind(changes.get("kind", title.kind))
        name, year = changes.get("name", title.name), changes.get("year", title.year)
        if (kind, name, year) != (title.kind, title.name, title.year):
            self._ensure_title_unique(kind, name, year, exclude_id=title.id)
        if kind is TitleKind.MOVIE and title.seasons:
            raise ConflictError("A title with seasons cannot become a movie", code="title_has_seasons")
        for field, value in changes.items():
            setattr(title, field, value)
        if data.genre_ids is not None:
            title.genres = self._resolve_genres(data.genre_ids)
        return TitleDetail.model_validate(title)

    def delete_title(self, title_id: int) -> None:
        title = self._get_title(title_id)
        poster_url = title.poster_url
        self.titles.delete(title)
        if poster_url:
            self.storage.delete(poster_url)

    def create_genre(self, data: GenreWrite) -> GenreRead:
        self._ensure_genre_unique(data.name)
        return GenreRead.model_validate(self.genres.add(Genre(name=data.name)))

    def update_genre(self, genre_id: int, data: GenreWrite) -> GenreRead:
        genre = self._get_genre(genre_id)
        self._ensure_genre_unique(data.name, exclude_id=genre.id)
        genre.name = data.name
        return GenreRead.model_validate(genre)

    def delete_genre(self, genre_id: int) -> None:
        self.genres.delete(self._get_genre(genre_id))

    def create_season(self, title_id: int, data: SeasonCreate) -> SeasonRead:
        title = self._get_title(title_id)
        if title.kind != TitleKind.SERIES:
            raise ConflictError("Seasons can only be added to series", code="not_a_series")
        self._ensure_season_unique(title.id, data.number)
        return SeasonRead.model_validate(self.seasons.add(Season(title_id=title.id, number=data.number)))

    def update_season(self, season_id: int, data: SeasonUpdate) -> SeasonRead:
        season = self._get_season(season_id)
        if data.number is not None and data.number != season.number:
            self._ensure_season_unique(season.title_id, data.number)
            season.number = data.number
        return SeasonRead.model_validate(season)

    def delete_season(self, season_id: int) -> None:
        self.seasons.delete(self._get_season(season_id))

    def create_episode(self, season_id: int, data: EpisodeCreate) -> EpisodeRead:
        season = self._get_season(season_id)
        self._ensure_episode_unique(season.id, data.number)
        episode = Episode(season_id=season.id, number=data.number, name=data.name)
        return EpisodeRead.model_validate(self.episodes.add(episode))

    def update_episode(self, episode_id: int, data: EpisodeUpdate) -> EpisodeRead:
        episode = self._get_episode(episode_id)
        if data.number is not None and data.number != episode.number:
            self._ensure_episode_unique(episode.season_id, data.number)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(episode, field, value)
        return EpisodeRead.model_validate(episode)

    def delete_episode(self, episode_id: int) -> None:
        self.episodes.delete(self._get_episode(episode_id))

    def _get_title(self, title_id: int) -> Title:
        if (title := self.titles.get(title_id)) is None:
            raise NotFoundError("Title not found", code="title_not_found")
        return title

    def _get_genre(self, genre_id: int) -> Genre:
        if (genre := self.genres.get(genre_id)) is None:
            raise NotFoundError("Genre not found", code="genre_not_found")
        return genre

    def _get_season(self, season_id: int) -> Season:
        if (season := self.seasons.get(season_id)) is None:
            raise NotFoundError("Season not found", code="season_not_found")
        return season

    def _get_episode(self, episode_id: int) -> Episode:
        if (episode := self.episodes.get(episode_id)) is None:
            raise NotFoundError("Episode not found", code="episode_not_found")
        return episode

    def _resolve_genres(self, genre_ids: Sequence[int]) -> list[Genre]:
        wanted = set(genre_ids)
        genres = list(self.genres.get_many(sorted(wanted)))
        missing = wanted - {g.id for g in genres}
        if missing:
            raise UnprocessableError(f"Unknown genre ids: {sorted(missing)}", code="unknown_genre")
        return sorted(genres, key=lambda g: g.name)

    def _ensure_title_unique(self, kind: TitleKind, name: str, year: int, exclude_id: int | None = None) -> None:
        existing = self.titles.get_by_identity(kind, name, year)
        if existing is not None and existing.id != exclude_id:
            raise ConflictError(f"{kind.capitalize()} '{name}' ({year}) already exists", code="title_exists")

    def _ensure_genre_unique(self, name: str, exclude_id: int | None = None) -> None:
        existing = self.genres.get_by_name(name)
        if existing is not None and existing.id != exclude_id:
            raise ConflictError(f"Genre '{existing.name}' already exists", code="genre_exists")

    def _ensure_season_unique(self, title_id: int, number: int) -> None:
        if self.seasons.get_by_number(title_id, number) is not None:
            raise ConflictError(f"Season {number} already exists", code="season_exists")

    def _ensure_episode_unique(self, season_id: int, number: int) -> None:
        if self.episodes.get_by_number(season_id, number) is not None:
            raise ConflictError(f"Episode {number} already exists", code="episode_exists")
