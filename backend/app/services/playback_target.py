from dataclasses import dataclass

from app.core.errors import NotFoundError, UnprocessableError
from app.models import Episode, Title, TitleKind
from app.services.ports import EntityStore


@dataclass(frozen=True)
class PlaybackTarget:
    title: Title
    episode: Episode | None

    @property
    def episode_id(self) -> int | None:
        return self.episode.id if self.episode else None


class PlaybackTargetResolver:
    def __init__(self, titles: EntityStore[Title], episodes: EntityStore[Episode]) -> None:
        self.titles = titles
        self.episodes = episodes

    def resolve(self, title_id: int, episode_id: int | None) -> PlaybackTarget:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("Title not found", code="title_not_found")
        if title.kind == TitleKind.MOVIE:
            if episode_id is not None:
                raise UnprocessableError("Movies have no episodes", code="episode_not_allowed")
            return PlaybackTarget(title, None)
        if episode_id is None:
            raise UnprocessableError("Choose an episode to play this series", code="episode_required")
        episode = self.episodes.get(episode_id)
        if episode is None or episode.season.title_id != title.id:
            raise NotFoundError("Episode not found in this series", code="episode_not_found")
        return PlaybackTarget(title, episode)
